"""Adversarial PostgreSQL W3.1-B executor tests."""
from __future__ import annotations
import os, threading
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from core.migration_identity import MigrationIdentity
from persistence.migration_executor import MigrationBypassError, MigrationDefinition, MigrationExecutionError, MigrationSchemaMismatch, execute_migration, migration_hash
from persistence.schema_authority import CoreSchemaStateModel, CoreSchemaUpgradeModel, create_schema_authority_tables, initialize_schema
from persistence.schema_reconciler import Descriptor, physical_schema_fingerprint, observe
pytestmark = pytest.mark.skipif(not os.getenv("GERCHAIN_TEST_DATABASE_URL"), reason="GERCHAIN_TEST_DATABASE_URL is required")
@pytest.fixture()
def engine():
    engine=create_engine(os.environ["GERCHAIN_TEST_DATABASE_URL"],future=True)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS core CASCADE")); conn.execute(text("CREATE SCHEMA core"))
        conn.execute(text("DROP TABLE IF EXISTS core_migration_identity CASCADE")); conn.execute(text("DROP TABLE IF EXISTS core_schema_upgrade CASCADE")); conn.execute(text("DROP TABLE IF EXISTS core_schema_state CASCADE"))
    create_schema_authority_tables(engine)
    with Session(engine) as session:
        with session.begin(): initialize_schema(session,"CORE",1,physical_schema_fingerprint(Descriptor("w3.1-v1.1","CORE",())))
    yield engine
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS core CASCADE")); conn.execute(text("DROP TABLE IF EXISTS core_migration_identity CASCADE")); conn.execute(text("DROP TABLE IF EXISTS core_schema_upgrade CASCADE")); conn.execute(text("DROP TABLE IF EXISTS core_schema_state CASCADE"))
    engine.dispose()
def _definition(engine,migration_id="m-1",sql=None,expected_hash=None,from_version=1,to_version=2):
    statements=tuple(sql or ("CREATE TABLE core.migration_target (id bigint PRIMARY KEY, value text NOT NULL)",))
    if expected_hash is None:
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE core.migration_target (id bigint PRIMARY KEY, value text NOT NULL)")); expected_hash=physical_schema_fingerprint(observe(conn,"CORE")); conn.execute(text("DROP TABLE core.migration_target"))
    return MigrationDefinition(MigrationIdentity(migration_id,"CORE",from_version,to_version,migration_hash(statements)),statements,expected_hash)
def _authority(engine):
    with Session(engine) as session: return session.get(CoreSchemaStateModel,"CORE"),session.query(CoreSchemaUpgradeModel).all()
def test_transactional_success_updates_physical_and_authority(engine):
    d=_definition(engine)
    with Session(engine) as s:
        with s.begin(): r=execute_migration(s,d)
    state,upgrades=_authority(engine); assert r.status.value=="APPLIED" and state.current_version==2 and len(upgrades)==1
    with engine.connect() as c: assert c.execute(text("SELECT to_regclass('core.migration_target')")).scalar()=='core.migration_target'
def test_same_id_committed_retry_does_not_execute_ddl_twice(engine):
    d=_definition(engine)
    with Session(engine) as s:
        with s.begin(): execute_migration(s,d)
    with Session(engine) as s:
        with s.begin(): execute_migration(s,d)
    state,upgrades=_authority(engine); assert state.current_version==2 and len(upgrades)==1
def test_same_id_changed_hash_is_rejected(engine):
    d=_definition(engine)
    with Session(engine) as s:
        with s.begin(): execute_migration(s,d)
    sql=("CREATE TABLE core.migration_target (id bigint PRIMARY KEY, other text NOT NULL)",); c=MigrationDefinition(MigrationIdentity("m-1","CORE",1,2,migration_hash(sql)),sql,d.expected_schema_hash)
    with Session(engine) as s:
        with s.begin():
            with pytest.raises(Exception,match="migration identity conflict"): execute_migration(s,c)
def test_distinct_upgrade_from_stale_predecessor_is_rejected_before_ddl(engine):
    d=_definition(engine)
    with Session(engine) as s:
        with s.begin(): execute_migration(s,d)
    sql=("CREATE TABLE core.migration_target_two (id bigint PRIMARY KEY)",); d2=MigrationDefinition(MigrationIdentity("m-2","CORE",1,2,migration_hash(sql)),sql,d.expected_schema_hash)
    with Session(engine) as s:
        with s.begin():
            with pytest.raises(MigrationExecutionError,match="stale schema predecessor"): execute_migration(s,d2)
    with engine.connect() as c: assert c.execute(text("SELECT to_regclass('core.migration_target_two')")).scalar() is None
def test_ddl_failure_rolls_back_physical_schema_and_authority(engine):
    sql=("CREATE TABLE core.migration_target (id bigint PRIMARY KEY)","CREATE TABLE core.migration_target (id bigint PRIMARY KEY)"); d=_definition(engine,sql=sql,expected_hash="f"*64)
    with Session(engine) as s:
        with pytest.raises(Exception):
            with s.begin(): execute_migration(s,d)
    state,upgrades=_authority(engine); assert state.current_version==1 and upgrades==[]
    with engine.connect() as c: assert c.execute(text("SELECT to_regclass('core.migration_target')")).scalar() is None
def test_actual_schema_mismatch_rolls_back_and_does_not_advance_authority(engine):
    d=_definition(engine,expected_hash="0"*64)
    with Session(engine) as s:
        with pytest.raises(MigrationSchemaMismatch):
            with s.begin(): execute_migration(s,d)
    state,upgrades=_authority(engine); assert state.current_version==1 and upgrades==[]
    with engine.connect() as c: assert c.execute(text("SELECT to_regclass('core.migration_target')")).scalar() is None
def test_bypass_is_rejected_before_database_mutation(engine):
    d=_definition(engine,sql=("DROP TABLE core.migration_target",))
    with Session(engine) as s:
        with s.begin():
            with pytest.raises(MigrationBypassError): execute_migration(s,d)
    state,upgrades=_authority(engine); assert state.current_version==1 and upgrades==[]
def test_unsafe_operations_are_rejected_before_database_mutation(engine):
    for sql in ("ALTER TABLE core.migration_target DROP COLUMN value","ALTER TABLE core.migration_target RENAME TO renamed","ALTER TABLE core.migration_target SET SCHEMA public","CREATE TABLE IF NOT EXISTS core.migration_target (id bigint PRIMARY KEY)","CREATE INDEX CONCURRENTLY idx_target ON core.migration_target (id)"):
        d=_definition(engine,migration_id=f"unsafe-{hash(sql)}",sql=(sql,))
        with Session(engine) as s:
            with s.begin():
                with pytest.raises(MigrationBypassError): execute_migration(s,d)
    state,upgrades=_authority(engine); assert state.current_version==1 and upgrades==[]
def test_concurrent_same_identity_serializes_and_only_one_applies(engine):
    d=_definition(engine); barrier=threading.Barrier(2); results=[]; errors=[]
    def worker():
        try:
            with Session(engine) as s:
                with s.begin(): barrier.wait(timeout=10); results.append(execute_migration(s,d).status.value)
        except Exception as exc: errors.append(exc)
    threads=[threading.Thread(target=worker) for _ in range(2)]
    for t in threads:t.start()
    for t in threads:t.join(timeout=20)
    assert not errors and results==["APPLIED","APPLIED"]
    state,upgrades=_authority(engine); assert state.current_version==2 and len(upgrades)==1
