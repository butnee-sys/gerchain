from __future__ import annotations

import hashlib
from contextlib import nullcontext
from pathlib import Path


MIGRATION_LOCK_KEY = 73546501


def checksum(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def _transaction(conn):
    """Support both SQLAlchemy and native psycopg connections."""
    if hasattr(conn, "begin"):
        return conn.begin()
    if hasattr(conn, "transaction"):
        return conn.transaction()
    return nullcontext()


def _execute(conn, sql: str, params=None):
    if hasattr(conn, "exec_driver_sql"):
        return conn.exec_driver_sql(sql, params or ())
    return conn.execute(sql, params or ())


def apply_migrations(conn, migration_dir: str | Path) -> None:
    """Apply migrations atomically for SQLAlchemy or native psycopg connections."""
    path = Path(migration_dir)
    files = sorted(path.glob("*.sql"))

    with _transaction(conn):
        _execute(
            conn,
            "SELECT pg_advisory_xact_lock(%s)",
            (MIGRATION_LOCK_KEY,),
        )
        _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version BIGINT PRIMARY KEY,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )

        rows = _execute(
            conn,
            "SELECT version, checksum FROM schema_version ORDER BY version",
        ).fetchall()
        applied = {int(row[0]): row[1] for row in rows}

        for migration in files:
            version = int(migration.name.split("_", 1)[0])
            sql = migration.read_text(encoding="utf-8")
            digest = checksum(sql)

            if version in applied:
                if applied[version] != digest:
                    raise RuntimeError(
                        f"Migration checksum mismatch for version {version}"
                    )
                continue

            _execute(conn, sql)
            _execute(
                conn,
                """
                INSERT INTO schema_version(version, checksum)
                VALUES (%s, %s)
                ON CONFLICT (version) DO NOTHING
                """,
                (version, digest),
            )
            recorded = _execute(
                conn,
                "SELECT checksum FROM schema_version WHERE version = %s",
                (version,),
            ).fetchone()
            if recorded is None or recorded[0] != digest:
                raise RuntimeError(
                    f"Migration checksum mismatch for version {version}"
                )
