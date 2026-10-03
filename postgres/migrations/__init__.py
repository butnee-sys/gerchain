from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy import text


def apply_migrations(connection, migration_dir: Path) -> None:
    migration_files = sorted(
        migration_dir.glob("*.sql"),
        key=lambda path: int(path.name.split("_", 1)[0]),
    )

    # Serialize the entire migration lifecycle at the PostgreSQL transaction level.
    # The xact-scoped lock cannot survive beyond the migration transaction and
    # therefore makes the schema_version read/DDL/record sequence one critical section.
    lock_key = "gerchain:migrations"
    connection.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
        {"lock_key": lock_key},
    )
    try:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version BIGINT PRIMARY KEY,
                    checksum TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )

        applied = {
            int(row[0]): row[1]
            for row in connection.execute(
                text("SELECT version, checksum FROM schema_version")
            )
        }

        for path in migration_files:
            version = int(path.name.split("_", 1)[0])
            sql = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()

            if version in applied:
                if applied[version] != checksum:
                    raise RuntimeError(
                        f"migration checksum mismatch for version {version}: {path.name}"
                    )
                continue

            connection.exec_driver_sql(sql)
            # Record the migration idempotently even when another migrator
            # committed the same version while this transaction was waiting on
            # the advisory lock. Keep the already-recorded checksum authoritative.
            recorded = connection.execute(
                text(
                    "INSERT INTO schema_version(version, checksum) "
                    "VALUES (:version, :checksum) "
                    "ON CONFLICT (version) DO NOTHING "
                    "RETURNING checksum"
                ),
                {"version": version, "checksum": checksum},
            ).scalar_one_or_none()
            if recorded is None:
                recorded = connection.execute(
                    text("SELECT checksum FROM schema_version WHERE version = :version"),
                    {"version": version},
                ).scalar_one()
            if recorded != checksum:
                raise RuntimeError(
                    f"migration checksum mismatch for version {version}: {path.name}"
                )
    finally:
        # pg_advisory_xact_lock is released automatically on transaction end.
        pass
