from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest

from postgres.migrations import apply_migrations


@pytest.mark.postgres
def test_failed_migration_rolls_back_ddl_and_schema_version(tmp_path: Path):
    """A failed SQL migration must leave neither its DDL nor history row."""
    database_url = os.environ.get("GERCHAIN_TEST_POSTGRES_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_POSTGRES_URL is not configured")

    schema = "migration_rollback_" + uuid4().hex
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_failure.sql").write_text(
        "CREATE TABLE rollback_probe (id INTEGER PRIMARY KEY);\n"
        "THIS IS NOT VALID SQL;",
        encoding="utf-8",
    )

    with psycopg.connect(database_url, autocommit=True) as admin:
        admin.execute(f'CREATE SCHEMA "{schema}"')

    try:
        with psycopg.connect(
            database_url,
            options=f"-c search_path={schema}",
        ) as connection:
            with pytest.raises(psycopg.Error):
                apply_migrations(connection, migrations)

            # The runner's transaction must have rolled back both the table
            # creation and the schema_version ledger publication.
            tables = connection.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = %s AND table_name = 'rollback_probe'",
                (schema,),
            ).fetchall()
            assert tables == []

            history_exists = connection.execute(
                "SELECT to_regclass(%s)",
                (f"{schema}.schema_version",),
            ).fetchone()[0]
            assert history_exists is None
    finally:
        with psycopg.connect(database_url, autocommit=True) as admin:
            admin.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
