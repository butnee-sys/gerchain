"""PostgreSQL-only migration race and checksum fail-closed tests.

Set GERCHAIN_TEST_DATABASE_URL to an isolated test PostgreSQL database.
Each test uses a private schema and never mutates public schema objects.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import psycopg
import pytest

from postgres.migrations import apply_migrations


DATABASE_URL = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="GERCHAIN_TEST_DATABASE_URL is required for real PostgreSQL migration tests",
)


def _connect(schema: str):
    connection = psycopg.connect(DATABASE_URL)
    connection.execute(f'SET search_path TO "{schema}"')
    connection.commit()
    return connection


def _make_schema() -> str:
    schema = "migration_test_" + uuid4().hex
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(f'CREATE SCHEMA "{schema}"')
    return schema


def _drop_schema(schema: str) -> None:
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')


def _migration_dir(root: Path, sql: str) -> Path:
    directory = root / "migrations"
    directory.mkdir()
    (directory / "001_probe.sql").write_text(sql, encoding="utf-8")
    return directory


def test_same_migration_started_concurrently_publishes_one_schema_version_row():
    schema = _make_schema()
    try:
        with TemporaryDirectory() as temporary:
            directory = _migration_dir(
                Path(temporary), "CREATE TABLE migration_race_probe (id INTEGER PRIMARY KEY);"
            )

            def run_once():
                with _connect(schema) as connection:
                    return apply_migrations(connection, directory)

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: run_once(), range(2)))

            with _connect(schema) as connection:
                rows = connection.execute(
                    "SELECT version, checksum FROM schema_version WHERE version = 1"
                ).fetchall()
                table_count = connection.execute(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = %s AND table_name = 'migration_race_probe'",
                    (schema,),
                ).fetchone()[0]

            assert len(rows) == 1, rows
            assert table_count == 1
            assert sorted(len(result) for result in results) == [0, 1]
    finally:
        _drop_schema(schema)


def test_changed_checksum_for_published_version_fails_closed():
    schema = _make_schema()
    try:
        with TemporaryDirectory() as temporary:
            directory = _migration_dir(
                Path(temporary), "CREATE TABLE migration_checksum_probe (id INTEGER PRIMARY KEY);"
            )
            with _connect(schema) as connection:
                assert apply_migrations(connection, directory) == (1,)

            migration = directory / "001_probe.sql"
            migration.write_text(
                "CREATE TABLE migration_checksum_probe (id INTEGER PRIMARY KEY, note TEXT);",
                encoding="utf-8",
            )
            with _connect(schema) as connection:
                with pytest.raises(RuntimeError, match="checksum mismatch"):
                    apply_migrations(connection, directory)

            with _connect(schema) as connection:
                version_rows = connection.execute(
                    "SELECT version, checksum FROM schema_version WHERE version = 1"
                ).fetchall()
                columns = connection.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = %s AND table_name = 'migration_checksum_probe' "
                    "ORDER BY ordinal_position",
                    (schema,),
                ).fetchall()
            assert len(version_rows) == 1
            assert [row[0] for row in columns] == ["id"]
    finally:
        _drop_schema(schema)
