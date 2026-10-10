"""Serialized PostgreSQL migration runner.

Each migration filename is its immutable version key. A transaction-scoped
advisory lock prevents concurrent runners from applying or publishing the same
version twice. SQL files must be safe to execute in one PostgreSQL transaction.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import psycopg
from psycopg import Connection

# Stable signed 64-bit key reserved for GerChain schema migrations.
_MIGRATION_LOCK_KEY = 731946205821


def apply_migrations(connection: Connection, migration_dir: Path) -> tuple[str, ...]:
    if connection.closed:
        raise ValueError("migration connection must be open")
    directory = Path(migration_dir)
    if not directory.is_dir():
        raise FileNotFoundError(f"migration directory does not exist: {directory}")

    applied_now: list[str] = []
    # Explicit transaction makes lock, DDL, and version publication atomic.
    with connection.transaction():
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (_MIGRATION_LOCK_KEY,))
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS gerchain_schema_migrations (
                version TEXT PRIMARY KEY,
                checksum_sha256 TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        for path in sorted(directory.glob("*.sql")):
            sql = path.read_text(encoding="utf-8")
            if not sql.strip():
                raise ValueError(f"empty migration is not allowed: {path.name}")
            import hashlib
            checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
            row = connection.execute(
                "SELECT checksum_sha256 FROM gerchain_schema_migrations WHERE version = %s",
                (path.name,),
            ).fetchone()
            if row is not None:
                if row[0] != checksum:
                    raise RuntimeError(f"applied migration checksum changed: {path.name}")
                continue
            connection.execute(sql)
            connection.execute(
                "INSERT INTO gerchain_schema_migrations(version, checksum_sha256) VALUES (%s, %s)",
                (path.name, checksum),
            )
            applied_now.append(path.name)
    return tuple(applied_now)


__all__ = ["apply_migrations"]
