"""Live PostgreSQL verification for the serialized migration runner.

Set GERCHAIN_TEST_DATABASE_URL to an isolated PostgreSQL database to execute.
These tests intentionally skip rather than silently substitute SQLite.
"""
from __future__ import annotations

import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, text

from persistence.migration_runner import Migration, apply_migrations


DATABASE_URL = os.environ.get("GERCHAIN_TEST_DATABASE_URL")


pytestmark = pytest.mark.postgres


@pytest.fixture
def pg_engine():
    if not DATABASE_URL:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is not configured")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    if engine.dialect.name != "postgresql":
        engine.dispose()
        pytest.fail("GERCHAIN_TEST_DATABASE_URL must point to PostgreSQL")
    try:
        yield engine
    finally:
        engine.dispose()


def _version() -> int:
    # schema_version is shared by all migration tests; use a fresh positive version.
    return 1_000_000_000 + uuid.uuid4().int % 1_000_000_000


def test_concurrent_migration_runners_apply_one_version_once(pg_engine):
    version = _version()
    suffix = uuid.uuid4().hex[:12]
    table_name = f"migration_concurrency_{suffix}"
    migration = Migration(
        version=version,
        sql=f"CREATE TABLE {table_name} (id INTEGER PRIMARY KEY)",
    )
    barrier = threading.Barrier(2)

    def run():
        # Independent Engine instances force independent PostgreSQL connections.
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        try:
            barrier.wait(timeout=10)
            return apply_migrations(engine, [migration])
        finally:
            engine.dispose()

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: run(), range(2)))

        assert sorted(results, key=len) == [(), (version,)]
        with pg_engine.connect() as connection:
            rows = connection.execute(
                text("SELECT version, checksum, applied_at FROM schema_version WHERE version=:v"),
                {"v": version},
            ).all()
            assert len(rows) == 1
            assert rows[0].checksum == migration.checksum
            assert connection.execute(
                text("SELECT to_regclass(:name)"), {"name": table_name}
            ).scalar_one() == table_name
    finally:
        with pg_engine.begin() as connection:
            connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            connection.execute(text("DELETE FROM schema_version WHERE version=:v"), {"v": version})


def test_replay_preserves_version_checksum_and_applied_at(pg_engine):
    version = _version()
    suffix = uuid.uuid4().hex[:12]
    table_name = f"migration_replay_{suffix}"
    migration = Migration(version=version, sql=f"CREATE TABLE {table_name} (id INTEGER)")
    try:
        assert apply_migrations(pg_engine, [migration]) == (version,)
        with pg_engine.connect() as connection:
            before = connection.execute(
                text("SELECT version, checksum, applied_at FROM schema_version WHERE version=:v"),
                {"v": version},
            ).one()

        assert apply_migrations(pg_engine, [migration]) == ()
        with pg_engine.connect() as connection:
            after = connection.execute(
                text("SELECT version, checksum, applied_at FROM schema_version WHERE version=:v"),
                {"v": version},
            ).one()
        assert tuple(after) == tuple(before)
    finally:
        with pg_engine.begin() as connection:
            connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            connection.execute(text("DELETE FROM schema_version WHERE version=:v"), {"v": version})


def test_checksum_mismatch_does_not_change_schema_or_history(pg_engine):
    version = _version()
    suffix = uuid.uuid4().hex[:12]
    table_name = f"migration_checksum_{suffix}"
    original = Migration(version=version, sql=f"CREATE TABLE {table_name} (id INTEGER)")
    changed = Migration(version=version, sql=f"CREATE TABLE {table_name} (id INTEGER, extra TEXT)")
    try:
        assert apply_migrations(pg_engine, [original]) == (version,)
        with pg_engine.connect() as connection:
            before = connection.execute(
                text("SELECT version, checksum, applied_at FROM schema_version WHERE version=:v"),
                {"v": version},
            ).one()
            columns_before = connection.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name=:name ORDER BY ordinal_position"),
                {"name": table_name},
            ).scalars().all()

        with pytest.raises(RuntimeError, match="migration checksum mismatch"):
            apply_migrations(pg_engine, [changed])

        with pg_engine.connect() as connection:
            after = connection.execute(
                text("SELECT version, checksum, applied_at FROM schema_version WHERE version=:v"),
                {"v": version},
            ).one()
            columns_after = connection.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name=:name ORDER BY ordinal_position"),
                {"name": table_name},
            ).scalars().all()

        assert tuple(after) == tuple(before)
        assert columns_after == columns_before == ["id"]
    finally:
        with pg_engine.begin() as connection:
            connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            connection.execute(text("DELETE FROM schema_version WHERE version=:v"), {"v": version})
