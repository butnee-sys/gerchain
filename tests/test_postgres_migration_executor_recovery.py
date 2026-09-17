from __future__ import annotations

import os
from datetime import datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from persistence.migration_executor import MigrationSchemaMismatch, execute_migration
from persistence.schema_authority import CoreSchemaStateModel, CoreSchemaUpgradeModel, create_schema_authority_tables, initialize_schema
from persistence.schema_reconciler import Descriptor, physical_schema_fingerprint

from tests.test_postgres_migration_executor import _authority, _definition


pytestmark = pytest.mark.skipif(
    not os.getenv("GERCHAIN_TEST_DATABASE_URL"),
    reason="GERCHAIN_TEST_DATABASE_URL is required",
)


@pytest.fixture()
def engine():
    engine = create_engine(os.environ["GERCHAIN_TEST_DATABASE_URL"], future=True)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS core CASCADE"))
        conn.execute(text("CREATE SCHEMA core"))
        conn.execute(text("DROP TABLE IF EXISTS core_schema_upgrade CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS core_schema_state CASCADE"))
    create_schema_authority_tables(engine)
    with Session(engine) as session:
        with session.begin():
            initialize_schema(session, "CORE", 1, physical_schema_fingerprint(Descriptor("w3.1-v1.1", "CORE", ())))
    yield engine
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS core CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS core_schema_upgrade CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS core_schema_state CASCADE"))
    engine.dispose()


def test_reader_sees_only_committed_migration_state(engine):
    definition = _definition(engine)
    with Session(engine) as session:
        tx = session.begin()
        execute_migration(session, definition)
        with engine.connect() as reader:
            assert reader.execute(text("SELECT current_version FROM core_schema_state WHERE schema_id='CORE'")).scalar() == 1
            assert reader.execute(text("SELECT to_regclass('core.migration_target')")).scalar() is None
        tx.commit()
    with engine.connect() as reader:
        assert reader.execute(text("SELECT current_version FROM core_schema_state WHERE schema_id='CORE'")).scalar() == 2
        assert reader.execute(text("SELECT to_regclass('core.migration_target')")).scalar() == 'core.migration_target'


def test_committed_authority_without_physical_schema_is_not_accepted(engine):
    definition = _definition(engine)
    with Session(engine) as session:
        with session.begin():
            session.add(
                CoreSchemaUpgradeModel(
                    upgrade_id=definition.identity.migration_id,
                    schema_id="CORE",
                    from_version=1,
                    to_version=2,
                    migration_hash=definition.identity.migration_hash,
                    authority=definition.authority,
                    status="APPLIED",
                    created_at=datetime.utcnow(),
                    applied_at=datetime.utcnow(),
                )
            )
            state = session.get(CoreSchemaStateModel, "CORE")
            state.current_version = 2
    with Session(engine) as session:
        with pytest.raises(MigrationSchemaMismatch):
            with session.begin():
                execute_migration(session, definition)


def test_failed_migration_can_be_retried_from_intact_predecessor(engine):
    bad = _definition(
        engine,
        migration_id="m-retry",
        sql=(
            "CREATE TABLE core.retry_target (id bigint PRIMARY KEY)",
            "CREATE TABLE core.retry_target (id bigint PRIMARY KEY)",
        ),
        expected_hash="f" * 64,
    )
    with Session(engine) as session:
        with pytest.raises(Exception):
            with session.begin():
                execute_migration(session, bad)

    good = _definition(
        engine,
        migration_id="m-retry",
        sql=("CREATE TABLE core.retry_target (id bigint PRIMARY KEY)",),
    )
    with Session(engine) as session:
        with session.begin():
            result = execute_migration(session, good)
    assert result.status.value == "APPLIED"
    state, upgrades = _authority(engine)
    assert state.current_version == 2
    assert len(upgrades) == 1


def test_physical_ddl_without_authority_is_rejected_not_adopted(engine):
    definition = _definition(engine)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE core.migration_target (id bigint PRIMARY KEY, value text NOT NULL)"))
    with Session(engine) as session:
        with pytest.raises(MigrationSchemaMismatch, match="recorded predecessor mismatch"):
            with session.begin():
                execute_migration(session, definition)
    state, upgrades = _authority(engine)
    assert state.current_version == 1
    assert upgrades == []
    with engine.connect() as conn:
        assert conn.execute(text("SELECT to_regclass('core.migration_target')")).scalar() == 'core.migration_target'


def test_external_unexpected_schema_does_not_get_silently_authorized(engine):
    definition = _definition(engine)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE core.unexpected (id bigint PRIMARY KEY)"))
    with Session(engine) as session:
        with pytest.raises(MigrationSchemaMismatch, match="recorded predecessor mismatch"):
            with session.begin():
                execute_migration(session, definition)
    state, upgrades = _authority(engine)
    assert state.current_version == 1
    assert upgrades == []
