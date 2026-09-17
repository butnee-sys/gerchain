from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from persistence.migration_executor import MigrationSchemaMismatch, execute_migration
from persistence.schema_authority import CoreSchemaStateModel, CoreSchemaUpgradeModel

from tests.test_postgres_migration_executor import _authority, _definition


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
                    created_at=__import__("datetime").datetime.utcnow(),
                    applied_at=__import__("datetime").datetime.utcnow(),
                )
            )
            state = session.get(CoreSchemaStateModel, "CORE")
            state.current_version = 2
    with Session(engine) as session:
        with pytest.raises(MigrationSchemaMismatch):
            with session.begin():
                execute_migration(session, definition)


def test_preapplied_matching_ddl_is_reconciled_and_authorized(engine):
    definition = _definition(engine)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE core.migration_target (id bigint PRIMARY KEY, value text NOT NULL)"))
    with Session(engine) as session:
        with session.begin():
            result = execute_migration(session, definition)
    state, upgrades = _authority(engine)
    assert result.status.value == "APPLIED"
    assert state.current_version == 2
    assert len(upgrades) == 1
