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
