"""Real-PostgreSQL migration locking and checksum integration test.

Set GERCHAIN_TEST_POSTGRES_URL to a disposable PostgreSQL database. This test
writes to public.schema_version and creates a probe table; never point it at
production. The migration runner's directory is monkeypatched to an isolated
temporary directory, so repository migrations are not applied by this test.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from persistence import schema_migrations


@pytest.mark.postgres
def test_concurrent_migration_is_applied_once_and_checksum_is_immutable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_url = os.environ.get("GERCHAIN_TEST_POSTGRES_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_POSTGRES_URL is not configured")
    if not database_url.startswith(
        ("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")
    ):
        pytest.fail("GERCHAIN_TEST_POSTGRES_URL must point to PostgreSQL")

    version = 987654321
    filename = f"{version}_concurrency_probe.sql"
    migration = tmp_path / filename
    probe_table = "gerchain_migration_concurrency_probe"
    migration.write_text(
        f"CREATE TABLE {probe_table} (id INTEGER PRIMARY KEY);\n"
        f"INSERT INTO {probe_table} (id) VALUES (1);\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(schema_migrations, "MIGRATION_DIR", tmp_path)

    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        # Require a clean, dedicated test database for this version/table.
        with engine.begin() as connection:
            connection.execute(text(
                "CREATE TABLE IF NOT EXISTS schema_version ("
                "version BIGINT PRIMARY KEY, checksum TEXT NOT NULL, "
                "applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            ))
            existing = connection.execute(
                text("SELECT version FROM schema_version WHERE version=:v"),
                {"v": version},
            ).scalar_one_or_none()
            if existing is not None:
                pytest.fail(
                    f"test migration version {version} already exists; "
                    "use a disposable PostgreSQL database"
                )
            table_exists = connection.execute(
                text("SELECT to_regclass(:name)"),
                {"name": f"public.{probe_table}"},
            ).scalar_one_or_none()
            if table_exists is not None:
                pytest.fail(
                    f"{probe_table} already exists; use a disposable PostgreSQL database"
                )

        # Independent connections/engines contend on the same advisory lock.
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(
                schema_migrations.apply_migrations,
                [database_url, database_url],
            ))

        assert sorted(len(result) for result in results) == [0, 1]
        with engine.connect() as connection:
            rows = connection.execute(
                text("SELECT checksum FROM schema_version WHERE version=:v"),
                {"v": version},
            ).all()
            assert len(rows) == 1
            assert connection.execute(
                text(f"SELECT count(*) FROM {probe_table}")
            ).scalar_one() == 1

        # Applied migration files are immutable: a changed checksum must fail closed.
        migration.write_text(
            migration.read_text(encoding="utf-8")
            + "\n-- intentional checksum mutation\n",
            encoding="utf-8",
        )
        with pytest.raises(RuntimeError, match="migration checksum mismatch"):
            schema_migrations.apply_migrations(database_url)

        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT count(*) FROM schema_version WHERE version=:v"),
                {"v": version},
            ).scalar_one() == 1
            assert connection.execute(
                text(f"SELECT count(*) FROM {probe_table}")
            ).scalar_one() == 1
    finally:
        # Cleanup only this test's uniquely versioned row and probe table.
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM schema_version WHERE version=:v"),
                {"v": version},
            )
            connection.execute(text(f"DROP TABLE IF EXISTS {probe_table}"))
        engine.dispose()
