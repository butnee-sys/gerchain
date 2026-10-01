from __future__ import annotations

import os
import hashlib
import json

import pytest
from sqlalchemy import text

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


@pytest.mark.integration
def test_production_factory_builds_real_postgresql_runtime():
    database_url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required")

    from sqlalchemy import create_engine
    engine = create_engine(database_url, pool_pre_ping=True)
    runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="FACTORY-PG-ESC",
            amount=100,
            currency="MNT",
            witness_id="FACTORY-PG-W",
        ),
        engine=engine,
    ).create()

    assert runtime.runtime_mode == "production-postgresql"
    assert runtime.is_canonical_ledger_authoritative is True
    runtime.require_canonical_ledger_authority()
    assert runtime._canonical_ledger is not None
    assert runtime._session_factory is not None
    engine.dispose()


@pytest.mark.integration
def test_production_factory_executes_canonical_ledger_value_flow_on_real_postgresql():
    database_url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required")

    from sqlalchemy import create_engine
    engine = create_engine(database_url, pool_pre_ping=True)
    runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="FACTORY-PG-FLOW",
            amount=100,
            currency="MNT",
            witness_id="FACTORY-PG-W-FLOW",
        ),
        engine=engine,
    ).create()

    ledger = runtime._canonical_ledger
    assert ledger is not None

    with runtime._session_factory() as session:
        ledger.create_account_in_transaction(session, "FACTORY-PG-FLOW-SOURCE", "MNT", 1000)
        ledger.create_account_in_transaction(session, "FACTORY-PG-FLOW-DEST", "MNT", 0)
        session.commit()

    material = json.dumps({
        "transaction_id": "PG-FLOW-1",
        "operation": "SETTLEMENT",
        "escrow_id": None,
        "source": "FACTORY-PG-FLOW-SOURCE",
        "destination": "FACTORY-PG-FLOW-DEST",
        "amount": 100,
        "currency": "MNT",
    }, sort_keys=True, separators=(",", ":"))
    integrity_hash = hashlib.sha256(material.encode()).hexdigest()

    with runtime._session_factory() as session:
        first = ledger.transfer_in_transaction(
            session,
            transaction_id="PG-FLOW-1",
            source="FACTORY-PG-FLOW-SOURCE",
            destination="FACTORY-PG-FLOW-DEST",
            amount=100,
            currency="MNT",
            operation="SETTLEMENT",
            escrow_id=None,
            integrity_hash=integrity_hash,
        )
        session.commit()

    assert first["replayed"] is False

    with runtime._session_factory() as session:
        replay = ledger.transfer_in_transaction(
            session,
            transaction_id="PG-FLOW-1",
            source="FACTORY-PG-FLOW-SOURCE",
            destination="FACTORY-PG-FLOW-DEST",
            amount=100,
            currency="MNT",
            operation="SETTLEMENT",
            escrow_id=None,
            integrity_hash=integrity_hash,
        )
        session.rollback()

    assert replay.get("replayed") is True

    source = runtime.get_balance("FACTORY-PG-FLOW-SOURCE")
    destination = runtime.get_balance("FACTORY-PG-FLOW-DEST")
    assert source == 900
    assert destination == 100
    engine.dispose()


@pytest.mark.integration
def test_production_factory_applies_canonical_schema_migrations():
    database_url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required")

    from sqlalchemy import create_engine
    engine = create_engine(database_url, pool_pre_ping=True)
    ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="FACTORY-PG-SCHEMA",
            amount=100,
            currency="MNT",
            witness_id="FACTORY-PG-W-SCHEMA",
        ),
        engine=engine,
    ).create()

    with engine.connect() as connection:
        versions = [
            row[0]
            for row in connection.execute(
                text("SELECT version FROM schema_version ORDER BY version")
            ).fetchall()
        ]
        assert versions == list(range(1, 12))

        for table in (
            "gerchain_ledger_accounts",
            "gerchain_ledger_movements",
            "gerchain_transaction_witnesses",
            "gerchain_idempotency_records",
            "gerchain_outbox_events",
        ):
            assert connection.execute(
                text("SELECT to_regclass(:table_name)"),
                {"table_name": table},
            ).scalar_one() == table

    engine.dispose()
