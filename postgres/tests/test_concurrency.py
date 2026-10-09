from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
import uuid

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg import sql

from postgres.migrations import apply_migrations


def _dsn() -> str:
    # psycopg accepts PostgreSQL DSNs, not SQLAlchemy driver-qualified URLs.
    value = os.environ.get("GERCHAIN_POSTGRES_DSN") or os.environ.get("GERCHAIN_DATABASE_URL") or os.environ["GERCHAIN_TEST_DATABASE_URL"]
    return value.replace("postgresql+psycopg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")


def _run_migrations() -> None:
    with psycopg.connect(_dsn()) as conn:
        apply_migrations(
            conn,
            Path(__file__).resolve().parents[1] / "migrations",
        )


def test_migrations_are_serialized_and_checksum_is_stable(monkeypatch):
    # EA-35.49: create a dedicated empty database so earlier tests cannot
    # accidentally pre-apply migrations and invalidate the concurrency proof.
    admin_dsn = _dsn()
    database_name = f"gerchain_migration_test_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name))
        )

    fresh_dsn = make_conninfo(admin_dsn, dbname=database_name)
    monkeypatch.setenv("GERCHAIN_POSTGRES_DSN", fresh_dsn)
    try:
        # Two independent sessions race the same truly fresh PostgreSQL database.
        # The migration runner must serialize publication and leave exactly one
        # authoritative schema_version row per version.
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(_run_migrations) for _ in range(2)]
            for future in futures:
                future.result()

        with psycopg.connect(_dsn()) as conn:
            rows = conn.execute(
                "SELECT version, checksum FROM schema_version ORDER BY version"
            ).fetchall()

        versions = [row[0] for row in rows]
        assert versions == sorted(set(versions)), "duplicate schema_version publication"
        assert versions
        assert max(versions) >= 13
        assert all(checksum for _, checksum in rows)

        # Re-run the publisher and prove both the version set and each checksum
        # are unchanged after a second complete migration pass.
        _run_migrations()
        with psycopg.connect(_dsn()) as conn:
            rows_after = conn.execute(
                "SELECT version, checksum FROM schema_version ORDER BY version"
            ).fetchall()
        assert rows_after == rows
    finally:
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            admin.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                    sql.Identifier(database_name)
                )
            )
