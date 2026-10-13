from __future__ import annotations

"""Focused PostgreSQL-only verification for the canonical migration chain.

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
import shutil
import tempfile
import time
import uuid
from pathlib import Path

import psycopg

from postgres.migrations import apply_migrations, checksum, _split_sql_statements, _canonical_migration_files

MIGRATION_DIR = Path(__file__).resolve().parents[1] / "postgres" / "migrations"
EXPECTED = tuple(range(1, len(_canonical_migration_files(MIGRATION_DIR)) + 1))
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
        # 0. Failed migration rollback, then corrected SQL at the SAME version.
        # The failed statement follows successful DDL in the same migration so
        # PostgreSQL must roll back both the DDL and schema_version publication.
        rollback_schema = new_schema("rollback_retry")
        with tempfile.TemporaryDirectory(prefix="gerchain-migration-rollback-") as temp_dir:
            retry_dir = Path(temp_dir)
            retry_file = retry_dir / "900_retry_probe.sql"
            retry_file.write_text(
                "CREATE TABLE migration_rollback_probe (id INTEGER PRIMARY KEY);\n"
                "THIS IS INTENTIONALLY INVALID SQL;\n",
                encoding="utf-8",
            )
            failed_error = None
            try:
                with _connect(base_url, rollback_schema) as conn:
                    apply_migrations(conn, retry_dir)
            except Exception as exc:
                failed_error = f"{type(exc).__name__}: {exc}"
            if not failed_error:
                raise AssertionError("intentionally invalid migration unexpectedly succeeded")
            with _connect(base_url, rollback_schema) as conn:
                table_after_failure = conn.execute(
                    "SELECT to_regclass('migration_rollback_probe')"
                ).fetchone()[0]
                registry_after_failure = conn.execute(
                    "SELECT to_regclass('schema_version')"
                ).fetchone()[0]
                conn.commit()
            if table_after_failure is not None or registry_after_failure is not None:
                raise AssertionError(
                    "failed migration left DDL or registry behind: "
                    f"table={table_after_failure}, registry={registry_after_failure}"
                )

            # Correct the SQL without changing the migration version/filename.
            retry_file.write_text(
                "CREATE TABLE migration_rollback_probe (id INTEGER PRIMARY KEY);\n"
                "INSERT INTO migration_rollback_probe(id) VALUES (1);\n",
                encoding="utf-8",
            )
            with _connect(base_url, rollback_schema) as conn:
                applied_retry = apply_migrations(conn, retry_dir)
            if applied_retry != (900,):
                raise AssertionError(
                    f"corrected same-version migration expected applied=(900,), got {applied_retry}"
                )
            with _connect(base_url, rollback_schema) as conn:
                probe_rows = conn.execute(
                    "SELECT id FROM migration_rollback_probe ORDER BY id"
                ).fetchall()
                registry_rows = conn.execute(
                    "SELECT version, checksum FROM schema_version ORDER BY version"
                ).fetchall()
                conn.commit()
            corrected_digest = checksum(retry_file.read_text(encoding="utf-8"))
            if probe_rows != [(1,)] or registry_rows != [(900, corrected_digest)]:
                raise AssertionError(
                    "corrected migration state mismatch: "
                    f"probe_rows={probe_rows}, registry_rows={registry_rows}"
                )
            with _connect(base_url, rollback_schema) as conn:
                already_applied = apply_migrations(conn, retry_dir)
            if already_applied != ():
                raise AssertionError(
                    f"same-version retry expected already-applied=(), got {already_applied}"
                )
            report["scenarios"]["failed_migration_rollback_and_same_version_retry"] = {
                "status": "PASS",
                "migration_version": 900,
                "failure": {
                    "result": "rolled-back",
                    "error": failed_error,
                    "ddl_absent_after_failure": table_after_failure is None,
                    "schema_version_absent_after_failure": registry_after_failure is None,
                },
                "corrected_retry": {
                    "result": "applied",
                    "applied_versions": list(applied_retry),
                    "checksum_matches_corrected_sql": registry_rows == [(900, corrected_digest)],
                    "probe_rows": [row[0] for row in probe_rows],
                },
                "repeat_retry": {
                    "result": "already-applied",
                    "applied_versions": list(already_applied),
                },
            }

        # 1. Empty PostgreSQL schema: all canonical migrations apply in order.
        clean = new_schema("clean")
        with _connect(base_url, clean) as conn:
            first = apply_migrations(conn, MIGRATION_DIR)
        if first != EXPECTED:
            raise AssertionError(f"clean first run expected {EXPECTED}, got {first}")
        report["scenarios"]["clean_first_run"] = {
            "status": "PASS", "applied_versions": list(first)
        }

        # 2. Idempotency: the same canonical migration chain must produce an exact NOOP.
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
            # Materialize version-1 DDL first, then emulate a legacy registry
            # whose duplicate publication rows predate its unique constraint.
            for statement in _split_sql_statements(source):
                conn.execute(statement)
            conn.execute("DROP TABLE schema_version")
            conn.execute("CREATE TABLE schema_version (version INTEGER, checksum TEXT, applied_at TIMESTAMPTZ DEFAULT now())")
            conn.execute("INSERT INTO schema_version(version, checksum) VALUES (1, %s), (1, %s)", (digest, digest))
            conn.commit()
        with _connect(base_url, legacy) as conn:
            applied = apply_migrations(conn, MIGRATION_DIR)
        if applied != tuple(range(2, len(EXPECTED) + 1)):
            raise AssertionError(f"legacy duplicate registry expected versions 2..{len(EXPECTED)}, got {applied}")
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
        if len(rows) != len(EXPECTED) or duplicate_count or not unique:
            raise AssertionError(f"legacy registry was not normalized to {len(EXPECTED)} unique version rows")
        report["scenarios"]["legacy_registry_duplicates"] = {
            "status": "PASS", "rows_after": len(rows), "duplicate_versions": duplicate_count,
            "unique_version_index": unique, "applied_versions": list(applied)
        }

        # 4. Reproduce legacy state-constraint drift at the boundary before migration 015.
        # Apply exactly versions 001-014, add a stale generated-style state CHECK as if
        # a legacy bootstrap had reintroduced it, then prove the 015/016 repair chain removes it and validates
        # the canonical lifecycle CHECK. Reapplying the full chain must be a NOOP.
        drift_schema = new_schema("state_drift")
        with tempfile.TemporaryDirectory(prefix="gerchain-migrations-001-014-") as temp_dir:
            legacy_dir = Path(temp_dir)
            for path in _canonical_migration_files(MIGRATION_DIR):
                if int(path.name.split("_", 1)[0]) <= 14:
                    shutil.copy2(path, legacy_dir / path.name)
            with _connect(base_url, drift_schema) as conn:
                applied_legacy = apply_migrations(conn, legacy_dir)
            if applied_legacy != tuple(range(1, 15)):
                raise AssertionError(f"legacy baseline expected versions 1..14, got {applied_legacy}")
        with _connect(base_url, drift_schema) as conn:
            conn.execute("""
                ALTER TABLE escrows
                ADD CONSTRAINT legacy_reintroduced_state_check
                CHECK (state IN ('CREATED', 'LOCKED', 'RELEASED'))
            """)
            conn.commit()
            stale_before = conn.execute("""
                SELECT conname, convalidated
                FROM pg_constraint
                WHERE conrelid = 'escrows'::regclass
                  AND contype = 'c'
                  AND lower(pg_get_constraintdef(oid)) LIKE '%state%'
                ORDER BY conname
            """).fetchall()
        if not any(row[0] == "legacy_reintroduced_state_check" for row in stale_before):
            raise AssertionError(f"stale legacy constraint was not reproduced: {stale_before}")
        with _connect(base_url, drift_schema) as conn:
            conn.commit()
            repaired = apply_migrations(conn, MIGRATION_DIR)
        if repaired != (15, 16):
            raise AssertionError(f"state drift repair expected migrations 015 and 016, got {repaired}")
        with _connect(base_url, drift_schema) as conn:
            checks = conn.execute("""
                SELECT conname, convalidated, pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'escrows'::regclass
                  AND contype = 'c'
                  AND lower(pg_get_constraintdef(oid)) LIKE '%state%'
                ORDER BY conname
            """).fetchall()
            conn.commit()
            second = apply_migrations(conn, MIGRATION_DIR)
        if len(checks) != 1 or checks[0][0] != "escrows_state_canonical_check" or checks[0][1] is not True:
            raise AssertionError(f"state constraint repair did not leave exactly one validated canonical CHECK: {checks}")
        if second != ():
            raise AssertionError(f"state drift repair second migration run must be NOOP, got {second}")
        report["scenarios"]["legacy_state_constraint_drift"] = {
            "status": "PASS",
            "baseline_versions": list(applied_legacy),
            "stale_constraint_before": [row[0] for row in stale_before],
            "repair_applied_versions": list(repaired),
            "state_constraints_after": [
                {"name": row[0], "validated": row[1], "definition": row[2]} for row in checks
            ],
            "second_run": "NOOP",
        }

        # 5. A conflicting checksum for an already-published version must fail closed
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

        # 6. Two independent runners against the same fresh schema: advisory lock
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
        labeled_results = [
            {"runner": "runner-1", "result": "applied", "versions": list(EXPECTED)},
            {"runner": "runner-2", "result": "already-applied", "versions": []},
        ]
        report["scenarios"]["concurrent_runners"] = {
            "status": "PASS",
            "raw_runner_results": results,
            "runner_results": labeled_results,
            "serialized_outcome": "exactly one applied; exactly one already-applied",
            "schema_version_duplicate_publications": 0,
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
