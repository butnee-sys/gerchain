"""Adversarial PostgreSQL W3.1-B executor tests.

These tests exercise the authority/executor boundary only. SHUUD is not
imported or involved.
"""
from __future__ import annotations

import os
import threading

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from core.migration_identity import MigrationIdentity
from persistence.migration_executor import (
    MigrationBypassError,
    MigrationDefinition,
    MigrationExecutionError,
    MigrationSchemaMismatch,
    execute_migration,
    migration_hash,
)
from persistence.schema_authority import (
    CoreSchemaStateModel,
    CoreSchemaUpgradeModel,
    create_schema_authority_tables,
    initialize_schema,
)
from persistence.schema_reconciler import Descriptor, physical_schema_fingerprint, observe


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


def _definition(engine, migration_id="m-1", sql=None, expected_hash=None, from_version=1, to_version=2):
    statements = tuple(sql or ("CREATE TABLE core.migration_target (id bigint PRIMARY KEY, value text NOT NULL)",))
    if expected_hash is None:
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE core.migration_target (id bigint PRIMARY KEY, value text NOT NULL)"))
            descriptor = observe(conn, "CORE")
            expected_hash = physical_schema_fingerprint(descriptor)
            conn.execute(text("DROP TABLE core.migration_target"))
    return MigrationDefinition(
        MigrationIdentity(migration_id, "CORE", from_version, to_version, migration_hash(statements)),
        statements,
        expected_hash,
    )


def _authority(engine):
    with Session(engine) as session:
        state = session.get(CoreSchemaStateModel, "CORE")
        upgrades = session.query(CoreSchemaUpgradeModel).all()
        return state, upgrades


def test_transactional_success_updates_physical_and_authority(engine):
    definition = _definition(engine)
    with Session(engine) as session:
        with session.begin():
            result = execute_migration(session, definition)
    state, upgrades = _authority(engine)
    assert result.status.value == "APPLIED"
    assert state.current_version == 2
    assert len(upgrades) == 1
    with engine.connect() as conn:
        assert conn.execute(text("SELECT 1 FROM core.migration_target")).scalar() == 1


def test_same_id_committed_retry_does_not_execute_ddl_twice(engine):
    definition = _definition(engine)
    with Session(engine) as session:
        with session.begin():
            execute_migration(session, definition)
    with Session(engine) as session:
        with session.begin():
            execute_migration(session, definition)
    state, upgrades = _authority(engine)
    assert state.current_version == 2
    assert len(upgrades) == 1


def test_same_id_changed_hash_is_rejected(engine):
    definition = _definition(engine)
    with Session(engine) as session:
        with session.begin():
            execute_migration(session, definition)
    changed_sql = ("CREATE TABLE core.migration_target (id bigint PRIMARY KEY, other text NOT NULL)",)
    conflict = MigrationDefinition(
        MigrationIdentity("m-1", "CORE", 1, 2, migration_hash(changed_sql)),
        changed_sql,
        definition.expected_schema_hash,
    )
    with Session(engine) as session:
        with session.begin():
            with pytest.raises(Exception, match="migration identity conflict"):
                execute_migration(session, conflict)


def test_distinct_upgrade_from_stale_predecessor_is_rejected_before_ddl(engine):
    definition = _definition(engine)
    with Session(engine) as session:
        with session.begin():
            execute_migration(session, definition)
    second_sql = ("CREATE TABLE core.migration_target_two (id bigint PRIMARY KEY)",)
    second = MigrationDefinition(
        MigrationIdentity("m-2", "CORE", 1, 2, migration_hash(second_sql)),
        second_sql,
        definition.expected_schema_hash,
    )
    with Session(engine) as session:
        with session.begin():
            with pytest.raises(MigrationExecutionError, match="stale schema predecessor"):
                execute_migration(session, second)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT to_regclass('core.migration_target_two')")).scalar() is None


def test_ddl_failure_rolls_back_physical_schema_and_authority(engine):
    statements = (
        "CREATE TABLE core.migration_target (id bigint PRIMARY KEY)",
        "CREATE TABLE core.migration_target (id bigint PRIMARY KEY)",
    )
    definition = _definition(engine, sql=statements, expected_hash="f" * 64)
    with Session(engine) as session:
        with pytest.raises(Exception):
            with session.begin():
                execute_migration(session, definition)
    state, upgrades = _authority(engine)
    assert state.current_version == 1
    assert upgrades == []
    with engine.connect() as conn:
        assert conn.execute(text("SELECT to_regclass('core.migration_target')")).scalar() is None


def test_actual_schema_mismatch_rolls_back_and_does_not_advance_authority(engine):
    definition = _definition(engine, expected_hash="0" * 64)
    with Session(engine) as session:
        with pytest.raises(MigrationSchemaMismatch):
            with session.begin():
                execute_migration(session, definition)
    state, upgrades = _authority(engine)
    assert state.current_version == 1
    assert upgrades == []
    with engine.connect() as conn:
        assert conn.execute(text("SELECT to_regclass('core.migration_target')")).scalar() is None


def test_bypass_is_rejected_before_database_mutation(engine):
    definition = _definition(engine, sql=("DROP TABLE core.migration_target",))
    with Session(engine) as session:
        with session.begin():
            with pytest.raises(MigrationBypassError):
                execute_migration(session, definition)
    state, upgrades = _authority(engine)
    assert state.current_version == 1
    assert upgrades == []


def test_concurrent_same_identity_serializes_and_only_one_applies(engine):
    definition = _definition(engine)
    barrier = threading.Barrier(2)
    results = []
    errors = []

    def worker():
        try:
            with Session(engine) as session:
                with session.begin():
                    barrier.wait(timeout=10)
                    results.append(execute_migration(session, definition).status.value)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    assert not errors
    assert results == ["APPLIED", "APPLIED"]
    state, upgrades = _authority(engine)
    assert state.current_version == 2
    assert len(upgrades) == 1
