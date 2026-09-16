from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from core.schema_authority import SchemaUpgrade
from persistence.schema_authority import (
    CoreSchemaStateModel,
    CoreSchemaUpgradeModel,
    SchemaUpgradeConflict,
    UpgradeStatus,
    apply_upgrade_transaction,
    create_schema_authority_tables,
    initialize_schema,
)
from database import get_database_engine


DB_URL = os.getenv("GERCHAIN_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DB_URL, reason="GERCHAIN_TEST_DATABASE_URL is required")


def _engine():
    return get_database_engine(DB_URL)


def _upgrade(upgrade_id: str, from_version: int = 1, to_version: int = 2) -> SchemaUpgrade:
    return SchemaUpgrade(
        upgrade_id=upgrade_id,
        schema_id="w3-test-schema",
        from_version=from_version,
        to_version=to_version,
        migration_hash=f"migration-{upgrade_id}",
        authority="core-test-authority",
    )


def _fresh_db():
    engine = _engine()
    create_schema_authority_tables(engine)
    CoreSchemaUpgradeModel.__table__.drop(engine, checkfirst=True)
    CoreSchemaStateModel.__table__.drop(engine, checkfirst=True)
    create_schema_authority_tables(engine)
    Session = sessionmaker(bind=engine)
    with Session.begin() as session:
        initialize_schema(session, "w3-test-schema", 1, "state-v1")
    return engine, Session


def test_w3_concurrent_distinct_upgrades_single_authority():
    engine, Session = _fresh_db()
    barrier = threading.Barrier(2)

    def worker(upgrade_id: str):
        session = Session()
        try:
            barrier.wait(timeout=10)
            result = apply_upgrade_transaction(session, _upgrade(upgrade_id), f"state-{upgrade_id}")
            session.commit()
            return result.status
        except Exception:
            session.rollback()
            return "REJECTED"
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, ["u-a", "u-b"]))

    session = Session()
    try:
        state = session.get(CoreSchemaStateModel, "w3-test-schema")
        upgrades = session.scalars(select(CoreSchemaUpgradeModel)).all()
        assert state.current_version == 2
        assert state.state_hash in {"state-u-a", "state-u-b"}
        assert sum(u.status == UpgradeStatus.APPLIED.value for u in upgrades) == 1
        assert sorted(results, key=str).count(UpgradeStatus.APPLIED) == 1
    finally:
        session.close()
        engine.dispose()


def test_w3_concurrent_same_upgrade_id_is_idempotent():
    engine, Session = _fresh_db()
    barrier = threading.Barrier(2)

    def worker():
        session = Session()
        try:
            barrier.wait(timeout=10)
            result = apply_upgrade_transaction(session, _upgrade("same-concurrent"), "state-v2")
            session.commit()
            return result.status
        except Exception:
            session.rollback()
            return "REJECTED"
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: worker(), range(2)))

    session = Session()
    try:
        state = session.get(CoreSchemaStateModel, "w3-test-schema")
        upgrades = session.scalars(select(CoreSchemaUpgradeModel)).all()
        assert results == [UpgradeStatus.APPLIED, UpgradeStatus.APPLIED]
        assert state.current_version == 2
        assert len(upgrades) == 1
    finally:
        session.close()
        engine.dispose()


def test_w3_same_upgrade_id_is_idempotent():
    engine, Session = _fresh_db()
    session = Session()
    try:
        first = apply_upgrade_transaction(session, _upgrade("same"), "state-v2")
        session.commit()
        second = apply_upgrade_transaction(session, _upgrade("same"), "state-v2")
        session.commit()
        assert first.status == UpgradeStatus.APPLIED
        assert second.status == UpgradeStatus.APPLIED
        assert session.query(CoreSchemaUpgradeModel).count() == 1
        assert session.get(CoreSchemaStateModel, "w3-test-schema").current_version == 2
    finally:
        session.close()
        engine.dispose()


def test_w3_stale_predecessor_is_rejected_without_mutation():
    engine, Session = _fresh_db()
    session = Session()
    try:
        apply_upgrade_transaction(session, _upgrade("u1"), "state-v2")
        session.commit()
        with pytest.raises(SchemaUpgradeConflict):
            apply_upgrade_transaction(session, _upgrade("u-stale"), "state-bad")
        session.rollback()
        state = session.get(CoreSchemaStateModel, "w3-test-schema")
        assert state.current_version == 2
        assert state.state_hash == "state-v2"
        assert session.get(CoreSchemaUpgradeModel, "u-stale") is None
    finally:
        session.close()
        engine.dispose()


def test_w3_failed_migration_rolls_back_authority_transition():
    engine, Session = _fresh_db()
    session = Session()
    try:
        apply_upgrade_transaction(session, _upgrade("u-fail"), "state-v2")
        raise RuntimeError("simulated migration failure after authority transition")
    except RuntimeError:
        session.rollback()
    finally:
        state = session.get(CoreSchemaStateModel, "w3-test-schema")
        assert state.current_version == 1
        assert state.state_hash == "state-v1"
        assert session.get(CoreSchemaUpgradeModel, "u-fail") is None
        session.close()
        engine.dispose()


def test_w3_reader_sees_only_committed_schema_state():
    engine, Session = _fresh_db()
    writer = Session()
    reader = Session()
    try:
        apply_upgrade_transaction(writer, _upgrade("u-reader"), "state-v2")
        # No writer commit yet: PostgreSQL's default READ COMMITTED reader must
        # continue to observe the predecessor state.
        before_commit = reader.get(CoreSchemaStateModel, "w3-test-schema")
        assert before_commit.current_version == 1
        assert before_commit.state_hash == "state-v1"
        writer.commit()
        reader.expire_all()
        after_commit = reader.get(CoreSchemaStateModel, "w3-test-schema")
        assert after_commit.current_version == 2
        assert after_commit.state_hash == "state-v2"
    finally:
        writer.rollback()
        writer.close()
        reader.close()
        engine.dispose()
