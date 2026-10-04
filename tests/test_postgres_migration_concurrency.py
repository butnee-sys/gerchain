from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, text

from postgres.migrations import apply_migrations


@pytest.mark.integration
def test_postgresql_migration_bootstrap_is_serialized():
    """Two first-boot workers must publish one consistent migration history."""
    database_url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required")

    from pathlib import Path

    migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "migrations"

    def bootstrap():
        engine = create_engine(database_url, pool_pre_ping=True)
        try:
            with engine.connect() as connection:
                apply_migrations(connection, migration_dir)
                return connection.execute(
                    text("SELECT version, checksum FROM schema_version ORDER BY version")
                ).fetchall()
        finally:
            engine.dispose()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.map(lambda _: bootstrap(), range(2))

    assert first == second
    assert [row[0] for row in first] == sorted(row[0] for row in first)
    assert len({row[0] for row in first}) == len(first)
