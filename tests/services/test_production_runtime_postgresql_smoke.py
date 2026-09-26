from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from persistence.atomic_ledger import LedgerAccountModel
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.production_schema_guard import assert_canonical_production_schema
from services.gerchain_runtime_factory import ProductionRuntimeFactory


def _factory():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL integration tests")
    engine = create_engine(url, pool_pre_ping=True)
    return engine


def test_production_factory_boots_and_uses_canonical_ledger():
    engine = _factory()
    runtime = ProductionRuntimeFactory.from_engine(
        escrow_id="SMOKE-ESCROW",
        amount=40,
        currency="MNT",
        witness_id="SMOKE-WITNESS",
        engine=engine,
    )

    assert runtime.is_canonical_ledger_authoritative
    with engine.begin() as connection:
        assert_canonical_production_schema(connection)

    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        session.add_all(
            [
                LedgerAccountModel(
                    account_id="SMOKE-SOURCE",
                    currency="MNT",
                    balance=100,
                    version=0,
                    updated_at=now,
                ),
                LedgerAccountModel(
                    account_id="SMOKE-ESCROW",
                    currency="MNT",
                    balance=0,
                    version=0,
                    updated_at=now,
                ),
                CanonicalEscrow(
                    id="SMOKE-ESCROW",
                    sender_address="SMOKE-SOURCE",
                    receiver_address="SMOKE-BENEFICIARY",
                    amount=40,
                    state=EscrowState.CREATED.value,
                    condition_desc=None,
                    refund_destination="SMOKE-SOURCE",
                    currency="MNT",
                    version=0,
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        session.commit()

    funded = runtime.fund(
        "SMOKE-FUND",
        "SMOKE-SOURCE",
        "SMOKE-T0",
        {"evidence": "production-postgresql"},
    )
    assert funded["replayed"] is False

    locked = runtime.lock(
        "SMOKE-LOCK",
        "SMOKE-T1",
        {"evidence": "production-postgresql"},
    )
    assert locked["replayed"] is False
    assert locked["value_movement"] is False

    released = runtime.release(
        transaction_id="SMOKE-RELEASE",
        destination="SMOKE-BENEFICIARY",
        timestamp="SMOKE-T2",
        evidence={"evidence": "production-postgresql"},
        root=object(),
        owner_id="SMOKE-OWNER",
        authorized=True,
        evidence_verified=True,
        trinity_proof={
            "trust": True,
            "transparency": True,
            "performance": True,
        },
        source="SMOKE-SOURCE",
    )
    assert released["replayed"] is False

    with Session(engine) as session:
        source = session.get(LedgerAccountModel, "SMOKE-SOURCE")
        escrow = session.get(LedgerAccountModel, "SMOKE-ESCROW")
        assert source is not None and source.balance == 60
        assert escrow is not None and escrow.balance == 0
        assert session.get(CanonicalEscrow, "SMOKE-ESCROW").state == "RELEASED"

    engine.dispose()
