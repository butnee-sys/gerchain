"""Serialized, atomic PostgreSQL SQL migration runner.

The advisory transaction lock serializes migration runners even when schema_version
is empty. The version row and the migration's DDL/data changes commit together.
This module deliberately requires PostgreSQL; it is not a SQLite fallback.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import Engine, text


_LOCK_NAMESPACE = 0x47455243  # "GERC"


@dataclass(frozen=True)
class Migration:
    version: int
    sql: str

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.sql.encode("utf-8")).hexdigest()


def apply_migrations(engine: Engine, migrations: Iterable[Migration]) -> tuple[int, ...]:
    """Apply pending migrations once, serially, with schema changes and version rows atomic."""
    if engine.dialect.name != "postgresql":
        raise ValueError("PostgreSQL is required for production schema migrations")

    ordered = sorted(migrations, key=lambda item: item.version)
    versions = [item.version for item in ordered]
    if any(version <= 0 for version in versions) or len(versions) != len(set(versions)):
        raise ValueError("migration versions must be unique positive integers")

    applied_now: list[int] = []
    # One transaction holds the advisory lock through DDL and schema_version updates.
    with engine.begin() as connection:
        connection.execute(
            text("SELECT pg_advisory_xact_lock(:namespace, :lock_id)"),
            {"namespace": _LOCK_NAMESPACE, "lock_id": 1},
        )
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version BIGINT PRIMARY KEY,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """))
        existing = {
            int(row.version): str(row.checksum)
            for row in connection.execute(
                text("SELECT version, checksum FROM schema_version ORDER BY version")
            )
        }

        for migration in ordered:
            checksum = migration.checksum
            if migration.version in existing:
                if existing[migration.version] != checksum:
                    raise RuntimeError(
                        f"migration checksum mismatch for version {migration.version}"
                    )
                continue

            # psycopg's DBAPI cursor accepts a migration SQL script containing multiple
            # statements. Keep it on this exact connection/transaction; never autocommit.
            raw_connection = connection.connection
            driver_connection = getattr(raw_connection, "driver_connection", raw_connection)
            with driver_connection.cursor() as cursor:
                cursor.execute(migration.sql)

            connection.execute(
                text("INSERT INTO schema_version (version, checksum) VALUES (:version, :checksum)"),
                {"version": migration.version, "checksum": checksum},
            )
            applied_now.append(migration.version)

    return tuple(applied_now)
