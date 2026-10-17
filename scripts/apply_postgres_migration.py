"""Apply a single PostgreSQL SQL migration with lock and checksum protection.

Usage:
  GERCHAIN_DATABASE_URL=postgresql+psycopg://... python -m scripts.apply_postgres_migration

The migration and its version row are committed in the same database transaction.
A session-level advisory lock serializes concurrent runners. A previously applied
version with a different checksum fails closed.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

from sqlalchemy import create_engine, text


MIGRATION_VERSION = 1
MIGRATION_PATH = Path(__file__).resolve().parents[1] / "postgres" / "schema" / "001_concurrency.sql"
ADVISORY_LOCK_KEY = 731_902_001


def apply_migration(database_url: str, migration_path: Path = MIGRATION_PATH) -> str:
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")):
        raise ValueError("PostgreSQL database URL is required")

    sql = migration_path.read_text(encoding="utf-8")
    checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
    engine = create_engine(database_url, pool_pre_ping=True)

    try:
        with engine.connect() as connection:
            # Session advisory lock survives transaction boundaries; explicit unlock
            # in finally avoids leaving a pooled connection holding the lock.
            connection.execute(text("SELECT pg_advisory_lock(:key)"), {"key": ADVISORY_LOCK_KEY})
            connection.commit()
            try:
                with connection.begin():
                    connection.execute(text("""
                        CREATE TABLE IF NOT EXISTS schema_version (
                            version BIGINT PRIMARY KEY,
                            checksum TEXT NOT NULL,
                            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                        )
                    """))
                    existing = connection.execute(
                        text("SELECT checksum FROM schema_version WHERE version = :version"),
                        {"version": MIGRATION_VERSION},
                    ).scalar_one_or_none()

                    if existing is not None:
                        if existing != checksum:
                            raise RuntimeError(
                                f"migration {MIGRATION_VERSION} checksum mismatch; refusing to continue"
                            )
                        return "ALREADY_APPLIED"

                    # Use the underlying DBAPI cursor so the SQL migration is executed
                    # as one unit inside this transaction, not split on semicolons
                    # (which would break on function bodies or quoted literals).
                    raw = connection.connection.driver_connection
                    with raw.cursor() as cursor:
                        cursor.execute(sql)
                    connection.execute(
                        text("""
                            INSERT INTO schema_version(version, checksum)
                            VALUES (:version, :checksum)
                        """),
                        {"version": MIGRATION_VERSION, "checksum": checksum},
                    )
                return "APPLIED"
            finally:
                connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": ADVISORY_LOCK_KEY})
                connection.commit()
    finally:
        engine.dispose()


def main() -> None:
    database_url = os.environ.get("GERCHAIN_DATABASE_URL", "")
    print(apply_migration(database_url))


if __name__ == "__main__":
    main()
