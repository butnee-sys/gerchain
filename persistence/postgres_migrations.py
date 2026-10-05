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

    The repository contains historical/alternative SQL files sharing migration
    numbers. Those files are not allowed to become production migration
    authority. Only this explicit canonical baseline is executable by the
    production runtime; checksum conflicts fail closed.
    """
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        raise ValueError("PostgreSQL database URL is required")

    root = Path(schema_dir) if schema_dir else Path(__file__).resolve().parents[1] / "postgres" / "schema"
    files = [root / name for name in _CANONICAL_BASELINE]
    if any(not path.is_file() for path in files):
        raise RuntimeError("canonical PostgreSQL production baseline is incomplete")

    applied: list[int] = []
    dsn = database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(dsn) as conn:
        first = files[0]
        first_sql = first.read_text(encoding="utf-8")
        first_checksum = hashlib.sha256(first_sql.encode("utf-8")).hexdigest()
        conn.execute(first_sql)
        conn.commit()

        for version, path in ((1, first), (2, files[1])):
            sql = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
            row = conn.execute(
                "SELECT checksum FROM schema_version WHERE version = %s",
                (version,),
            ).fetchone()
            if row is not None and row[0] != checksum:
                raise RuntimeError(f"canonical migration checksum mismatch: {path.name}")
            if row is None:
                conn.execute(sql)
                conn.execute(
                    "INSERT INTO schema_version(version, checksum) VALUES (%s, %s)",
                    (version, checksum),
                )
                conn.commit()
                applied.append(version)
    return applied
