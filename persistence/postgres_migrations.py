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
)


def apply_canonical_production_baseline(database_url: str, schema_dir: str | Path | None = None) -> list[int]:
    """Apply the single authoritative production schema baseline.

    Historical SQL files share migration numbers, so the generic legacy runner
    cannot be production authority. This explicit baseline is the only schema
    path used by the production runtime; checksum conflicts fail closed.
    """
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        raise ValueError("PostgreSQL database URL is required")

    root = Path(schema_dir) if schema_dir else Path(__file__).resolve().parents[1] / "postgres" / "schema"
    files = [root / name for name in _CANONICAL_BASELINE]
    if any(not path.is_file() for path in files):
        raise RuntimeError("canonical PostgreSQL production baseline is incomplete")

    checksums = {
        version: hashlib.sha256(path.read_bytes()).hexdigest()
        for version, path in ((1, files[0]), (2, files[1]))
    }
    dsn = database_url.replace("postgresql+psycopg://", "postgresql://")
    applied: list[int] = []

    with psycopg.connect(dsn) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(hashtext('gerchain:canonical-production-migrations'))")
        schema_exists = conn.execute(
            "SELECT to_regclass('public.schema_version')"
        ).fetchone()[0] is not None

        if not schema_exists:
            conn.execute(files[0].read_text(encoding="utf-8"))
            conn.execute(
                "INSERT INTO schema_version(version, checksum) VALUES (%s, %s)",
                (1, checksums[1]),
            )
            conn.commit()
            applied.append(1)
        else:
            row = conn.execute(
                "SELECT checksum FROM schema_version WHERE version = 1"
            ).fetchone()
            if row is None:
                raise RuntimeError("canonical migration baseline is not established")
            if row[0] != checksums[1]:
                raise RuntimeError("canonical migration checksum mismatch: 001_concurrency.sql")

        row = conn.execute(
            "SELECT checksum FROM schema_version WHERE version = 2"
        ).fetchone()
        if row is not None:
            if row[0] != checksums[2]:
                raise RuntimeError("canonical migration checksum mismatch: 002_canonical_production.sql")
        else:
            conn.execute(files[1].read_text(encoding="utf-8"))
            conn.execute(
                "INSERT INTO schema_version(version, checksum) VALUES (%s, %s)",
                (2, checksums[2]),
            )
            conn.commit()
            applied.append(2)

    return applied
