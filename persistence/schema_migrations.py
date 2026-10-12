"""Fail-closed PostgreSQL schema migration runner.

Migration files are ordered by filename under postgres/schema. Each file's SHA-256
is recorded in schema_version in the same transaction as the migration. A changed
file whose version is already recorded is rejected; do not edit applied migrations.
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from sqlalchemy import create_engine, text

MIGRATION_DIR = Path(__file__).resolve().parent / "postgres" / "schema"
MIGRATION_NAME = re.compile(r"^(\d{3,})_[a-zA-Z0-9_]+\.sql$")


def _checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def apply_migrations(database_url: str) -> list[str]:
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")):
        raise ValueError("migrations require a PostgreSQL URL")

    files = sorted(
        path for path in MIGRATION_DIR.iterdir()
        if path.is_file() and MIGRATION_NAME.match(path.name)
    )
    if not files:
        raise RuntimeError(f"no numbered migrations found in {MIGRATION_DIR}")

    engine = create_engine(database_url, pool_pre_ping=True)
    applied_now: list[str] = []
    try:
        with engine.begin() as connection:
            # Serialize all migration runners for this database.
            connection.execute(text("SELECT pg_advisory_xact_lock(741923, 20261012)"))
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version BIGINT PRIMARY KEY,
                    checksum TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """))

            # Fail closed before migration 001 can backfill legacy escrow rows.
            connection.exec_driver_sql("""
                DO $preflight$
                DECLARE
                    has_escrows BOOLEAN;
                    has_refund_destination BOOLEAN;
                    has_created_at BOOLEAN;
                    unsafe_rows BIGINT;
                BEGIN
                    SELECT to_regclass('public.escrows') IS NOT NULL INTO has_escrows;
                    IF has_escrows THEN
                        SELECT EXISTS (SELECT 1 FROM information_schema.columns
                            WHERE table_schema = 'public' AND table_name = 'escrows'
                              AND column_name = 'refund_destination') INTO has_refund_destination;
                        SELECT EXISTS (SELECT 1 FROM information_schema.columns
                            WHERE table_schema = 'public' AND table_name = 'escrows'
                              AND column_name = 'created_at') INTO has_created_at;
                        IF NOT has_refund_destination OR NOT has_created_at THEN
                            SELECT count(*) INTO unsafe_rows FROM escrows;
                            IF unsafe_rows > 0 THEN
                                RAISE EXCEPTION 'migration blocked: legacy escrow rows need reviewed refund_destination/created_at backfill';
                            END IF;
                        ELSE
                            SELECT count(*) INTO unsafe_rows FROM escrows
                             WHERE refund_destination IS NULL OR created_at IS NULL;
                            IF unsafe_rows > 0 THEN
                                RAISE EXCEPTION 'migration blocked: % escrow row(s) need reviewed backfill', unsafe_rows;
                            END IF;
                        END IF;
                    END IF;
                END
                $preflight$;
            """)
            for path in files:
                match = MIGRATION_NAME.match(path.name)
                assert match is not None
                version = int(match.group(1))
                raw = path.read_bytes()
                checksum = _checksum(raw)
                recorded = connection.execute(
                    text("SELECT checksum FROM schema_version WHERE version = :version"),
                    {"version": version},
                ).scalar_one_or_none()

                if recorded is not None:
                    if recorded != checksum:
                        raise RuntimeError(
                            f"migration checksum mismatch for {path.name}; "
                            "applied migration files are immutable"
                        )
                    continue

                # A version must never be silently skipped.
                lower_unapplied = connection.execute(
                    text("SELECT version FROM schema_version WHERE version > :version LIMIT 1"),
                    {"version": version},
                ).scalar_one_or_none()
                if lower_unapplied is not None:
                    raise RuntimeError(
                        f"out-of-order migration {path.name}; higher version "
                        f"{lower_unapplied} is already recorded"
                    )

                # Execute as a single transaction. SQL files must not contain
                # transaction-control statements of their own.
                connection.exec_driver_sql(raw.decode("utf-8"))
                connection.execute(
                    text("""
                        INSERT INTO schema_version (version, checksum)
                        VALUES (:version, :checksum)
                    """),
                    {"version": version, "checksum": checksum},
                )
                applied_now.append(path.name)
        return applied_now
    finally:
        engine.dispose()


def main() -> None:
    database_url = os.environ.get("GERCHAIN_DATABASE_URL", "")
    if not database_url:
        raise RuntimeError("GERCHAIN_DATABASE_URL is required")
    print("Applied migrations:", apply_migrations(database_url))


if __name__ == "__main__":
    main()
