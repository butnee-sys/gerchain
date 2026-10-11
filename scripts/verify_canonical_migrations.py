from __future__ import annotations

"""Focused PostgreSQL-only verification for the canonical 1..13 migration chain.

Run with GERCHAIN_MIGRATION_TEST_DATABASE_URL pointing to a disposable PostgreSQL
database. This intentionally does not invoke the general test suite, so unrelated
regressions cannot mask or contaminate migration-gate evidence.
"""
import concurrent.futures
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import psycopg

from postgres.migrations import apply_migrations, checksum

MIGRATION_DIR = Path(__file__).resolve().parents[1] / "postgres" / "migrations"
EXPECTED = tuple(range(1, 14))
REPORT_PATH = Path(os.environ.get("MIGRATION_GATE_REPORT", "migration-gate-report.json"))


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return os.environ.get("GITHUB_SHA", "UNKNOWN")


def _connect(base_url: str, schema: str):
    return psycopg.connect(base_url, options=f"-c search_path={schema}")


def _run() -> dict:
    base_url = os.environ.get("GERCHAIN_MIGRATION_TEST_DATABASE_URL")
    if not base_url or not base_url.startswith(("postgresql://", "postgres://")):
        raise RuntimeError("GERCHAIN_MIGRATION_TEST_DATABASE_URL must point to disposable PostgreSQL")
    base_url = base_url.replace("postgres://", "postgresql://", 1)
    report = {
        "commit_sha": _git_sha(),
        "migration_versions_expected": list(EXPECTED),
        "started_at_epoch": time.time(),
        "scenarios": {},
        "status": "IN_PROGRESS",
    }
    schemas: list[str] = []

    def new_schema(label: str) -> str:
        name = f"mig_gate_{label}_{uuid.uuid4().hex[:10]}"
        with psycopg.connect(base_url, autocommit=True) as conn:
            conn.execute(f'CREATE SCHEMA "{name}"')
        schemas.append(name)
        return name

    try:
        # 1. Empty PostgreSQL schema: all canonical migrations apply in order.
        clean = new_schema("clean")
        with _connect(base_url, clean) as conn:
            first = apply_migrations(conn, MIGRATION_DIR)
        if first != EXPECTED:
            raise AssertionError(f"clean first run expected {EXPECTED}, got {first}")
        report["scenarios"]["clean_first_run"] = {
            "status": "PASS", "applied_versions": list(first)
        }

        # 2. Idempotency: the same 13-file chain must produce an exact NOOP.
        with _connect(base_url, clean) as conn:
            second = apply_migrations(conn, MIGRATION_DIR)
        if second != ():
            raise AssertionError(f"second run must be NOOP, got {second}")
        report["scenarios"]["second_run_noop"] = {
            "status": "PASS", "applied_versions": list(second), "result": "NOOP"
        }

        # 3. Legacy schema_version without a unique key and identical duplicate
        # publications: the runner must collapse duplicates and establish uniqueness.
        legacy = new_schema("legacy")
        source = (MIGRATION_DIR / "001_canonical_production.sql").read_text(encoding="utf-8")
        digest = checksum(source)
        with _connect(base_url, legacy) as conn:
            conn.execute("CREATE TABLE schema_version (version INTEGER, checksum TEXT, applied_at TIMESTAMPTZ DEFAULT now())")
            conn.execute("INSERT INTO schema_version(version, checksum) VALUES (1, %s), (1, %s)", (digest, digest))
            conn.commit()
        with _connect(base_url, legacy) as conn:
            applied = apply_migrations(conn, MIGRATION_DIR)
        if applied != tuple(range(2, 14)):
            raise AssertionError(f"legacy duplicate registry expected versions 2..13, got {applied}")
        with _connect(base_url, legacy) as conn:
            rows = conn.execute("SELECT version, checksum FROM schema_version ORDER BY version").fetchall()
            duplicate_count = conn.execute("SELECT COUNT(*) FROM (SELECT version FROM schema_version GROUP BY version HAVING COUNT(*) > 1) d").fetchone()[0]
            unique = conn.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_index i JOIN pg_attribute a
                    ON a.attrelid=i.indrelid AND a.attnum=i.indkey[0]
                    WHERE i.indrelid='schema_version'::regclass AND i.indisunique
                    AND i.indpred IS NULL AND i.indnkeyatts=1 AND a.attname='version'
                )
            """).fetchone()[0]
        if len(rows) != 13 or duplicate_count or not unique:
            raise AssertionError("legacy registry was not normalized to 13 unique version rows")
        report["scenarios"]["legacy_registry_duplicates"] = {
            "status": "PASS", "rows_after": len(rows), "duplicate_versions": duplicate_count,
            "unique_version_index": unique, "applied_versions": list(applied)
        }

        # 4. A conflicting checksum for an already-published version must fail closed
        # and preserve the conflicting registry as evidence (no silent repair).
        drift = new_schema("checksum")
        with _connect(base_url, drift) as conn:
            conn.execute("CREATE TABLE schema_version (version INTEGER PRIMARY KEY, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ DEFAULT now())")
            conn.execute("INSERT INTO schema_version(version, checksum) VALUES (1, %s)", ("0" * 64,))
            conn.commit()
        error = None
        try:
            with _connect(base_url, drift) as conn:
                apply_migrations(conn, MIGRATION_DIR)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        if not error or "checksum mismatch" not in error.lower():
            raise AssertionError(f"expected checksum mismatch fail-closed, got {error!r}")
        with _connect(base_url, drift) as conn:
            stored = conn.execute("SELECT checksum FROM schema_version WHERE version=1").fetchone()[0]
        if stored != "0" * 64:
            raise AssertionError("checksum-conflict evidence was unexpectedly modified")
        report["scenarios"]["checksum_conflict"] = {
            "status": "PASS", "expected": "fail-closed", "observed_error": error,
            "stored_conflicting_checksum_preserved": True
        }

        # 5. Two independent runners against the same fresh schema: advisory lock
        # serializes execution; one applies all versions and the other observes NOOP.
        concurrent_schema = new_schema("concurrent")
        def runner():
            with _connect(base_url, concurrent_schema) as conn:
                return list(apply_migrations(conn, MIGRATION_DIR))
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: runner(), range(2)))
        normalized = sorted((tuple(result) for result in results), key=len, reverse=True)
        if normalized != [EXPECTED, ()]:
            raise AssertionError(f"concurrent runners expected one full apply and one NOOP, got {results}")
        report["scenarios"]["concurrent_runners"] = {
            "status": "PASS", "runner_results": results,
            "serialized_outcome": "one full apply; one NOOP"
        }

        report["status"] = "PASS"
        return report
    except Exception as exc:
        report["status"] = "FAIL"
        report["failure"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report["finished_at_epoch"] = time.time()
        # Preserve report even when a scenario fails. Keep scenario schemas
        # until evidence has been collected; disposable CI database is discarded.
        REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        _run()
    except Exception:
        sys.exit(1)
