from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerMovementModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


@pytest.mark.integration
def test_ea35_real_postgresql_fund_lock_release_and_deep_reconciliation():
    database_url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required")

    engine = create_engine(database_url, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="EA35-PG-ESCROW",
            amount=100,
            currency="MNT",
            witness_id="EA35-PG-WITNESS",
        ),
        engine=engine,
    ).create()

    ledger = runtime._canonical_ledger
    assert ledger is not None

    now = datetime.now(timezone.utc)
    with factory() as session:
        ledger.create_account_in_transaction(session, "EA35-SOURCE", "MNT", 1000)
        ledger.create_account_in_transaction(session, "EA35-PG-ESCROW", "MNT", 0)
        ledger.create_account_in_transaction(session, "EA35-BENEFICIARY", "MNT", 0)
        session.add(
            CanonicalEscrow(
                id="EA35-PG-ESCROW",
                sender_address="EA35-SOURCE",
                receiver_address="EA35-BENEFICIARY",
                amount=100,
                state="CREATED",
                condition_desc="EA35 production re-performance",
                refund_destination="EA35-SOURCE",
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

    with factory() as session:
        result = fund_escrow_in_transaction(
            session,
            transaction_id="EA35-FUND-1",
            escrow_id="EA35-PG-ESCROW",
            source="EA35-SOURCE",
            amount=100,
            currency="MNT",
        )
        assert result["replayed"] is False
        session.commit()

    with factory() as session:
        result = lock_escrow_in_transaction(
            session,
            transaction_id="EA35-LOCK-1",
            escrow_id="EA35-PG-ESCROW",
        )
        assert result["status"] == "LOCKED"
        session.commit()

    with factory() as session:
        result = release_escrow_in_transaction(
            session,
            transaction_id="EA35-RELEASE-1",
            escrow_id="EA35-PG-ESCROW",
            beneficiary="EA35-BENEFICIARY",
            amount=100,
            currency="MNT",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        assert result["replayed"] is False
        session.commit()

    with factory() as session:
        escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == "EA35-PG-ESCROW")
        ).scalar_one()
        report = deep_reconcile_value_truth(session)
        movements = list(session.execute(select(LedgerMovementModel)).scalars())
        assert escrow.state == "RELEASED"
        assert report.matched is True
        assert len(movements) == 2
        assert {m.operation for m in movements} == {"FUND", "RELEASE"}

    assert runtime.get_balance("EA35-SOURCE") == 900
    assert runtime.get_balance("EA35-PG-ESCROW") == 0
    assert runtime.get_balance("EA35-BENEFICIARY") == 100
    engine.dispose()
