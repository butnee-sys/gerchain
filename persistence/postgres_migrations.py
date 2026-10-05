"""Apply ordered PostgreSQL schema migrations exactly once.

Production deployments should run this before constructing the canonical runtime.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import psycopg


_VERSION_RE = re.compile(r"^(\d+)_.*\.sql$")


def apply_migrations(database_url: str, schema_dir: str | Path | None = None) -> list[int]:
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        raise ValueError("PostgreSQL database URL is required")

    root = Path(schema_dir) if schema_dir else Path(__file__).resolve().parents[1] / "postgres" / "schema"
    files = sorted(root.glob("*.sql"))
    if not files:
        raise RuntimeError(f"no PostgreSQL migrations found in {root}")

    applied: list[int] = []
    with psycopg.connect(database_url.replace("postgresql+psycopg://", "postgresql://")) as conn:
        for path in files:
            match = _VERSION_RE.match(path.name)
            if match is None:
                raise RuntimeError(f"invalid migration filename: {path.name}")
            version = int(match.group(1))
            sql = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()

            row = conn.execute(
                "SELECT checksum FROM schema_version WHERE version = %s",
                (version,),
            ).fetchone()
            if row is not None:
                if row[0] != checksum:
                    raise RuntimeError(f"migration checksum mismatch: {path.name}")
                continue

            conn.execute(sql)
            conn.execute(
                "INSERT INTO schema_version(version, checksum) VALUES (%s, %s)",
                (version, checksum),
            )
            conn.commit()
            applied.append(version)

    return applied


_CANONICAL_BASELINE = (
    "001_concurrency.sql",
    "002_canonical_production.sql",
    "003_canonical_integrity_constraints.sql",
    "004_ea26_value_flow_persistence.sql",
    "005_canonical_production.sql",
    "006_canonical_production.sql",
    "007_canonical_production.sql",
    "008_canonical_production.sql",
    "009_canonical_production.sql",
    "010_canonical_evidence_constraints.sql",
    "011_ea35_canonical_schema_finalization.sql",
)


def apply_canonical_production_baseline(database_url: str, schema_dir: str | Path | None = None) -> list[int]:
    """Apply the single authoritative production schema sequence, fail closed on drift."""
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        raise ValueError("PostgreSQL database URL is required")

    root = Path(schema_dir) if schema_dir else Path(__file__).resolve().parents[1] / "postgres" / "schema"
    files = [root / name for name in _CANONICAL_BASELINE]
    if any(not path.is_file() for path in files):
        raise RuntimeError("canonical PostgreSQL production baseline is incomplete")

    dsn = database_url.replace("postgresql+psycopg://", "postgresql://")
    applied: list[int] = []

    with psycopg.connect(dsn) as conn:
        conn.execute(
            "SELECT pg_advisory_xact_lock(hashtext('gerchain:canonical-production-migrations'))"
        )
        first_sql = files[0].read_text(encoding="utf-8")
        schema_exists = conn.execute(
            "SELECT to_regclass('public.schema_version')"
        ).fetchone()[0] is not None

        if not schema_exists:
            conn.execute(first_sql)
            # 001 creates schema_version; record its checksum in the same transaction.
            conn.execute(
                "INSERT INTO schema_version(version, checksum) VALUES (%s, %s)",
                (1, hashlib.sha256(first_sql.encode("utf-8")).hexdigest()),
            )
            conn.commit()
            applied.append(1)
        else:
            row = conn.execute("SELECT checksum FROM schema_version WHERE version = 1").fetchone()
            expected = hashlib.sha256(first_sql.encode("utf-8")).hexdigest()
            if row is None or row[0] != expected:
                raise RuntimeError("canonical migration baseline mismatch: 001_concurrency.sql")

        for version, path in enumerate(files[1:], start=2):
            sql = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
            row = conn.execute(
                "SELECT checksum FROM schema_version WHERE version = %s",
                (version,),
            ).fetchone()
            if row is not None:
                if row[0] != checksum:
                    raise RuntimeError(f"canonical migration checksum mismatch: {path.name}")
                continue
            conn.execute(sql)
            conn.execute(
                "INSERT INTO schema_version(version, checksum) VALUES (%s, %s)",
                (version, checksum),
            )
            conn.commit()
            applied.append(version)

    return applied
