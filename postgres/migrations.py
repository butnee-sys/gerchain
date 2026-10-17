from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

MIGRATION_LOCK_KEY = 73546501


def checksum(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def apply_migrations(conn, migration_dir: str | Path) -> None:
    """Apply migrations under a session-level advisory lock.

    The lock is acquired and committed before opening the DDL transaction.
    A session-level lock survives transaction/savepoint boundaries, preventing
    concurrent callers that already have an implicit transaction from applying
    the same migration version twice. The connection must be dedicated to this
    migration call; this function commits its own lock acquisition/unlock.
    """
    path = Path(migration_dir)
    files = sorted(path.glob("*.sql"))

    # Session lock is deliberately used instead of pg_advisory_xact_lock:
    # callers may arrive with an implicit transaction, turning transaction()
    # into a savepoint and weakening the intended serialization boundary.
    conn.execute("SELECT pg_advisory_lock(%s)", (MIGRATION_LOCK_KEY,))
    conn.commit()
    try:
        with conn.transaction():
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version BIGINT PRIMARY KEY,
                    checksum TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )

            rows = conn.execute(
                "SELECT version, checksum FROM schema_version ORDER BY version"
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

                conn.execute(sql)
                conn.execute(
                    "INSERT INTO schema_version(version, checksum) VALUES (%s, %s)",
                    (version, digest),
                )
                applied[version] = digest
    finally:
        # Always release the session lock, including when DDL/checksum fails.
        conn.execute("SELECT pg_advisory_unlock(%s)", (MIGRATION_LOCK_KEY,))
        conn.commit()
