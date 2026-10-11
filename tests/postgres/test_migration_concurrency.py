from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest

from postgres.migrations import apply_migrations


@pytest.mark.postgres
def test_two_connections_apply_migrations_without_duplicate_schema_versions(tmp_path: Path):
    """Integration test for serialized migration/version publication.

    Requires a disposable PostgreSQL database in GERCHAIN_TEST_POSTGRES_URL.
    The test creates and drops a uniquely named schema; it never touches public.
    """
    database_url = os.environ.get("GERCHAIN_TEST_POSTGRES_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_POSTGRES_URL is not configured")

    schema = "migration_race_" + uuid4().hex
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_first.sql").write_text(
        "CREATE TABLE migration_probe (id INTEGER PRIMARY KEY);",
        encoding="utf-8",
    )

    with psycopg.connect(database_url, autocommit=True) as admin:
        admin.execute(f'CREATE SCHEMA "{schema}"')

    try:
        def apply_once() -> tuple[int, ...]:
            # Each worker gets a separate physical connection and isolated
            # search_path, exercising PostgreSQL's cross-connection lock.
            with psycopg.connect(
                database_url,
                options=f"-c search_path={schema}",
            ) as connection:
                return apply_migrations(connection, migrations)

        # Exactly one worker applies version 1; the other observes it already
        # applied. Assert the documented return contract, not just absence of
        # an exception: one result is (1,), the other is (), i.e. counts [0, 1].
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(apply_once)
            second = pool.submit(apply_once)
            results = [first.result(timeout=30), second.result(timeout=30)]

        assert sorted(len(result) for result in results) == [0, 1]
        assert sorted(version for result in results for version in result) == [1]

        with psycopg.connect(database_url, options=f"-c search_path={schema}") as check:
            rows = check.execute(
                "SELECT version, checksum FROM schema_version ORDER BY version"
            ).fetchall()
            assert [row[0] for row in rows] == [1]
            assert len({row[0] for row in rows}) == 1
            assert len(rows) == 1
            assert check.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = 'migration_probe' "
                "ORDER BY ordinal_position",
                (schema,),
            ).fetchall() == [("id",)]
    finally:
        with psycopg.connect(database_url, autocommit=True) as admin:
            admin.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
