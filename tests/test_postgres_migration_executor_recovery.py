from __future__ import annotations
import os
from datetime import datetime
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from persistence.migration_executor import MigrationSchemaMismatch, execute_migration
from persistence.schema_authority import CoreSchemaStateModel, CoreSchemaUpgradeModel, create_schema_authority_tables, initialize_schema
from persistence.schema_reconciler import Descriptor, physical_schema_fingerprint, observe
from tests.test_postgres_migration_executor import _authority, _definition
pytestmark=pytest.mark.skipif(not os.getenv("GERCHAIN_TEST_DATABASE_URL"),reason="GERCHAIN_TEST_DATABASE_URL is required")
@pytest.fixture()
def engine():
    engine=create_engine(os.environ["GERCHAIN_TEST_DATABASE_URL"],future=True)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS core CASCADE")); conn.execute(text("CREATE SCHEMA core")); conn.execute(text("DROP TABLE IF EXISTS core_migration_identity CASCADE")); conn.execute(text("DROP TABLE IF EXISTS core_schema_upgrade CASCADE")); conn.execute(text("DROP TABLE IF EXISTS core_schema_state CASCADE"))
    create_schema_authority_tables(engine)
    with Session(engine) as s:
        with s.begin(): initialize_schema(s,"CORE",1,physical_schema_fingerprint(Descriptor("w3.1-v1.1","CORE",())))
    yield engine
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS core CASCADE")); conn.execute(text("DROP TABLE IF EXISTS core_migration_identity CASCADE")); conn.execute(text("DROP TABLE IF EXISTS core_schema_upgrade CASCADE")); conn.execute(text("DROP TABLE IF EXISTS core_schema_state CASCADE"))
    engine.dispose()
def _expected_hash_for_sql(engine,statement):
    with engine.begin() as conn:
        conn.execute(text(statement)); expected=physical_schema_fingerprint(observe(conn,"CORE")); table_name=statement.split("core.",1)[1].split(" ",1)[0]; conn.execute(text(f'DROP TABLE core."{table_name}"'))
    return expected
def test_reader_sees_only_committed_migration_state(engine):
    d=_definition(engine)
    with Session(engine) as s:
        tx=s.begin(); execute_migration(s,d)
        with engine.connect() as r:
            assert r.execute(text("SELECT current_version FROM core_schema_state WHERE schema_id='CORE'")).scalar()==1
            assert r.execute(text("SELECT to_regclass('core.migration_target')")).scalar() is None
        tx.commit()
    with engine.connect() as r:
        assert r.execute(text("SELECT current_version FROM core_schema_state WHERE schema_id='CORE'")).scalar()==2
        assert r.execute(text("SELECT to_regclass('core.migration_target')")).scalar()=='core.migration_target'
def test_committed_authority_without_physical_schema_is_not_accepted(engine):
    d=_definition(engine)
    with Session(engine) as s:
        with s.begin():
            s.add(CoreSchemaUpgradeModel(upgrade_id=d.identity.migration_id,schema_id="CORE",from_version=1,to_version=2,migration_hash=d.identity.migration_hash,authority=d.authority,status="APPLIED",created_at=datetime.utcnow(),applied_at=datetime.utcnow())); state=s.get(CoreSchemaStateModel,"CORE"); state.current_version=2
    with Session(engine) as s:
        with pytest.raises(MigrationSchemaMismatch):
            with s.begin(): execute_migration(s,d)
def test_failed_migration_preserves_predecessor_and_corrected_retry_uses_new_identity(engine):
    bad_sql=("CREATE TABLE core.retry_target (id bigint PRIMARY KEY)","CREATE TABLE core.retry_target (id bigint PRIMARY KEY)"); bad=_definition(engine,migration_id="m-retry-bad",sql=bad_sql,expected_hash="f"*64)
    with Session(engine) as s:
        with pytest.raises(Exception):
            with s.begin(): execute_migration(s,bad)
    state,upgrades=_authority(engine); assert state.current_version==1 and upgrades==[]
    with engine.connect() as c: assert c.execute(text("SELECT to_regclass('core.retry_target')")).scalar() is None
    good_sql=("CREATE TABLE core.retry_target (id bigint PRIMARY KEY)",); good=_definition(engine,migration_id="m-retry-good",sql=good_sql,expected_hash=_expected_hash_for_sql(engine,good_sql[0]))
    with Session(engine) as s:
        with s.begin(): result=execute_migration(s,good)
    assert result.status.value=="APPLIED"; state,upgrades=_authority(engine); assert state.current_version==2 and len(upgrades)==1
def test_same_identity_after_failed_transaction_cannot_change_payload(engine):
    bad_sql=("CREATE TABLE core.retry_conflict (id bigint PRIMARY KEY)","CREATE TABLE core.retry_conflict (id bigint PRIMARY KEY)"); bad=_definition(engine,migration_id="m-conflict",sql=bad_sql,expected_hash="f"*64)
    with Session(engine) as s:
        with pytest.raises(Exception):
            with s.begin(): execute_migration(s,bad)
    good_sql=("CREATE TABLE core.retry_conflict (id bigint PRIMARY KEY)",); good=_definition(engine,migration_id="m-conflict",sql=good_sql,expected_hash=_expected_hash_for_sql(engine,good_sql[0]))
    with Session(engine) as s:
        with s.begin():
            with pytest.raises(Exception,match="migration identity conflict"): execute_migration(s,good)
def test_physical_ddl_without_authority_is_rejected_not_adopted(engine):
    d=_definition(engine)
    with engine.begin() as conn: conn.execute(text("CREATE TABLE core.migration_target (id bigint PRIMARY KEY, value text NOT NULL)"))
    with Session(engine) as s:
        with pytest.raises(MigrationSchemaMismatch,match="recorded predecessor mismatch"):
            with s.begin(): execute_migration(s,d)
    state,upgrades=_authority(engine); assert state.current_version==1 and upgrades==[]
    with engine.connect() as c: assert c.execute(text("SELECT to_regclass('core.migration_target')")).scalar()=='core.migration_target'
def test_external_unexpected_schema_does_not_get_silently_authorized(engine):
    d=_definition(engine)
    with engine.begin() as conn: conn.execute(text("CREATE TABLE core.unexpected (id bigint PRIMARY KEY)"))
    with Session(engine) as s:
        with pytest.raises(MigrationSchemaMismatch,match="recorded predecessor mismatch"):
            with s.begin(): execute_migration(s,d)
    state,upgrades=_authority(engine); assert state.current_version==1 and upgrades==[]
