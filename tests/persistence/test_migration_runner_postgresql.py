from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import text

from persistence.migration_runner import Migration, apply_migrations


pytestmark = [pytest.mark.integration]


@pytest.fixture(autouse=True)
def _remove_synthetic_migration_versions(canonical_postgresql_engine):
    """Keep high-numbered migration-runner probes out of canonical schema history.

    These tests exercise the generic legacy runner with synthetic version IDs.
    The shared PostgreSQL fixture is also used by production tests that require
    exactly the canonical 1..13 migration registry, so probe rows and objects
    must be removed even when an assertion fails.
    """
    yield
    with canonical_postgresql_engine.begin() as connection:
        connection.execute(text(
            "DELETE FROM schema_version WHERE version IN (987654321, 987654322, 987654323)"
        ))
        connection.execute(text("DROP TABLE IF EXISTS migration_once_probe"))
        connection.execute(text("DROP TABLE IF EXISTS migration_checksum_probe"))
        connection.execute(text("DROP TABLE IF EXISTS migration_rollback_probe"))


def test_concurrent_runners_apply_one_version_once(canonical_postgresql_engine):
    engine = canonical_postgresql_engine
    migration = Migration(
        987654321,
        "CREATE TABLE IF NOT EXISTS migration_once_probe (id INTEGER PRIMARY KEY); "
        "INSERT INTO migration_once_probe (id) VALUES (1) ON CONFLICT (id) DO NOTHING;",
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: apply_migrations(engine, [migration]), range(2)))

    assert sorted(results, key=len) == [(), (987654321,)]
    with engine.connect() as connection:
        count = connection.execute(
            text("SELECT count(*) FROM migration_once_probe WHERE id = 1")
        ).scalar_one()
        version_count = connection.execute(
            text("SELECT count(*) FROM schema_version WHERE version = 987654321")
        ).scalar_one()
    assert count == 1
    assert version_count == 1


def test_failed_migration_does_not_record_version(canonical_postgresql_engine):
    engine = canonical_postgresql_engine
    migration = Migration(
        987654322,
        "CREATE TABLE migration_rollback_probe (id INTEGER PRIMARY KEY); "
        "INSERT INTO migration_table_that_does_not_exist (id) VALUES (1);",
    )
    with pytest.raises(Exception):
        apply_migrations(engine, [migration])

    with engine.connect() as connection:
        version_count = connection.execute(
            text("SELECT count(*) FROM schema_version WHERE version = 987654322")
        ).scalar_one()
        table_count = connection.execute(
            text("""
                SELECT count(*) FROM information_schema.tables
                WHERE table_schema = current_schema()
                  AND table_name = 'migration_rollback_probe'
            """)
        ).scalar_one()
    assert version_count == 0
    assert table_count == 0


def test_applied_version_checksum_is_immutable(canonical_postgresql_engine):
    engine = canonical_postgresql_engine
    first = Migration(987654323, "CREATE TABLE IF NOT EXISTS migration_checksum_probe (id INTEGER);")
    apply_migrations(engine, [first])
    changed = Migration(987654323, "CREATE TABLE IF NOT EXISTS migration_checksum_probe (id BIGINT);")
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        apply_migrations(engine, [changed])
