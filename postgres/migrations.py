from __future__ import annotations

import hashlib
from contextlib import nullcontext
from pathlib import Path

import psycopg.sql
from sqlalchemy import text


MIGRATION_LOCK_KEY = 73546501

# Version 004 previously shipped with explicit BEGIN/COMMIT wrappers. Keep its
# historical checksum accepted so existing databases can migrate to the
# runner-compatible source without rewriting schema history.
LEGACY_CHECKSUMS = {
    4: {"729c586234c0b630cce6edd9feab694f4d589dcb5e9321e44f7d22ab556799a0"},
}


def checksum(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def _transaction(conn):
    """Support both SQLAlchemy and native psycopg connections."""
    if hasattr(conn, "in_transaction"):
        return nullcontext() if conn.in_transaction() else conn.begin()
    if hasattr(conn, "begin"):
        return conn.begin()
    if hasattr(conn, "transaction"):
        return conn.transaction()
    return nullcontext()


def _execute(conn, sql: str, params=None):
    # Non-parameterized DDL/PLpgSQL may contain literal percent signs.
    # Avoid psycopg's pyformat parser when there are no parameters.
    if hasattr(conn, "exec_driver_sql"):
        if params is None:
            # SQLAlchemy's PostgreSQL driver still interprets literal % signs
            # when using exec_driver_sql. text() preserves PL/pgSQL format
            # strings such as format('%I', ...) as literal SQL.
            return conn.execute(text(sql))
        return conn.exec_driver_sql(sql, params)
    if params is None:
        # Native psycopg parses % as a placeholder even for literal DDL.
        # SQL() marks the migration as literal SQL without changing its source text.
        return conn.execute(psycopg.sql.SQL(sql))
    return conn.execute(sql, params)


def apply_migrations(conn, migration_dir: str | Path) -> None:
    """Apply migrations atomically for SQLAlchemy or native psycopg connections."""
    path = Path(migration_dir)
    files = sorted(path.glob("*.sql"))
    versions: dict[int, Path] = {}
    for migration in files:
        version = int(migration.name.split("_", 1)[0])
        if version in versions:
            raise RuntimeError(
                f"Duplicate migration version {version}: "
                f"{versions[version].name} and {migration.name}"
            )
        versions[version] = migration

    # Serialize the entire migration critical section at session level.
    # PostgreSQL releases this lock automatically if the session disappears.
    _execute(conn, "SELECT pg_advisory_lock(%s)", (MIGRATION_LOCK_KEY,))
    try:
        with _transaction(conn):
            _execute(conn, "SELECT pg_advisory_xact_lock(%s)", (MIGRATION_LOCK_KEY,))
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
                    if applied[version] != digest and applied[version] not in LEGACY_CHECKSUMS.get(version, set()):
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
    finally:
        _execute(conn, "SELECT pg_advisory_unlock(%s)", (MIGRATION_LOCK_KEY,))
