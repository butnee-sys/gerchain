from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest

from postgres.migrations import apply_migrations

MIGRATION_DIR = Path(__file__).resolve().parents[2] / "postgres" / "migrations"
EXPECTED_VERSIONS = list(range(1, 15))


@pytest.mark.postgres
def test_two_connections_apply_canonical_migrations_without_duplicate_schema_versions():
    """Exercise the full canonical 14-migration chain on concurrent connections.

    Requires a disposable PostgreSQL database in GERCHAIN_TEST_POSTGRES_URL.
    The test creates and drops a uniquely named schema; it never touches public.
    """
    database_url = os.environ.get("GERCHAIN_TEST_POSTGRES_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_POSTGRES_URL is not configured")

    schema = "migration_race_" + uuid4().hex
    with psycopg.connect(database_url, autocommit=True) as admin:
        admin.execute(f'CREATE SCHEMA "{schema}"')

    try:
        def apply_once() -> tuple[int, ...]:
            with psycopg.connect(
                database_url,
                options=f"-c search_path={schema}",
            ) as connection:
                return apply_migrations(connection, MIGRATION_DIR)

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(apply_once)
            second = pool.submit(apply_once)
            results = [first.result(timeout=180), second.result(timeout=180)]

        # The transaction-scoped advisory lock must allow exactly one runner to
        # apply the chain while the other sees it as already applied.
        assert sorted(len(result) for result in results) == [0, 14]
        assert sorted(version for result in results for version in result) == EXPECTED_VERSIONS

        with psycopg.connect(database_url, options=f"-c search_path={schema}") as check:
            rows = check.execute(
                "SELECT version, checksum FROM schema_version ORDER BY version"
            ).fetchall()
            assert [row[0] for row in rows] == EXPECTED_VERSIONS
            assert len(rows) == 14
            assert len({row[0] for row in rows}) == 14
            assert all(row[1] for row in rows)

            unique_version = check.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_index i
                    JOIN pg_class t ON t.oid = i.indrelid
                    JOIN pg_namespace n ON n.oid = t.relnamespace
                    JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = i.indkey[0]
                    WHERE n.nspname = %s
                      AND t.relname = 'schema_version'
                      AND i.indisunique
                      AND i.indpred IS NULL
                      AND i.indnkeyatts = 1
                      AND a.attname = 'version'
                )
                """,
                (schema,),
            ).fetchone()[0]
            assert unique_version is True

            state_constraints = check.execute(
                """
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = 'escrows'::regclass
                  AND contype = 'c'
                  AND pg_get_constraintdef(oid) ILIKE '%state%'
                ORDER BY conname
                """
            ).fetchall()
            assert len(state_constraints) == 1, (
                "canonical schema must have exactly one escrow state CHECK; "
                f"found={state_constraints!r}"
            )
            assert state_constraints[0][0] == "escrows_state_canonical_check"
    finally:
        with psycopg.connect(database_url, autocommit=True) as admin:
            admin.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')

@pytest.mark.postgres
def test_concurrent_bootstrap_creates_registry_once():
    """Prove repeated bootstrap preserves schema_version and every checksum."""
    database_url = os.environ.get("GERCHAIN_TEST_POSTGRES_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_POSTGRES_URL is not configured")

    schema = "migration_registry_" + uuid4().hex
    with psycopg.connect(database_url, autocommit=True) as admin:
        admin.execute(f'CREATE SCHEMA "{schema}"')

    try:
        with psycopg.connect(
            database_url, options=f"-c search_path={schema}"
        ) as connection:
            first_applied = apply_migrations(connection, MIGRATION_DIR)
        assert first_applied == tuple(EXPECTED_VERSIONS) or first_applied == EXPECTED_VERSIONS

        with psycopg.connect(database_url, options=f"-c search_path={schema}") as check:
            before = check.execute(
                "SELECT version, checksum FROM schema_version ORDER BY version"
            ).fetchall()
        assert [version for version, _ in before] == EXPECTED_VERSIONS
        assert all(checksum for _, checksum in before)

        with psycopg.connect(
            database_url, options=f"-c search_path={schema}"
        ) as connection:
            second_applied = apply_migrations(connection, MIGRATION_DIR)
        assert not second_applied

        with psycopg.connect(database_url, options=f"-c search_path={schema}") as check:
            after = check.execute(
                "SELECT version, checksum FROM schema_version ORDER BY version"
            ).fetchall()
        assert after == before
    finally:
        with psycopg.connect(database_url, autocommit=True) as admin:
            admin.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
