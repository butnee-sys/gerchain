from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness
from persistence.durable_idempotency import DurableIdempotencyRecord
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.recovery_outbox import OutboxEvent
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from services.gerchain_runtime import GerchainRuntime
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_real_postgresql_production_eai_flow():
    url = os.environ["GERCHAIN_TEST_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="PG-EAI-ESCROW",
            amount=100,
            currency="MNT",
            witness_id="PG-EAI-WITNESS",
        ),
        engine=engine,
    )
    runtime = factory.create()
    ledger = runtime._canonical_ledger
    assert ledger is not None

    now = datetime.now(timezone.utc)
    with runtime._session_factory() as session:
        ledger.create_account_in_transaction(session, "PG-EAI-SOURCE", "MNT", 1000)
        ledger.create_account_in_transaction(session, "PG-EAI-ESCROW", "MNT", 0)
        ledger.create_account_in_transaction(session, "PG-EAI-BENEFICIARY", "MNT", 0)
        session.add(
            CanonicalEscrow(
                id="PG-EAI-ESCROW",
                sender_address="PG-EAI-SOURCE",
                receiver_address="PG-EAI-BENEFICIARY",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="production-smoke",
                refund_destination="PG-EAI-SOURCE",
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

    funded = runtime.fund(
        "PG-EAI-FUND",
        "PG-EAI-SOURCE",
        "PG-EAI-T0",
        {"verified": True},
    )
    assert funded["replayed"] is False

    locked = runtime.lock(
        "PG-EAI-LOCK",
        "PG-EAI-T1",
        {"verified": True},
    )
    assert locked["replayed"] is False

    released = runtime.release(
        transaction_id="PG-EAI-RELEASE",
        destination="PG-EAI-BENEFICIARY",
        timestamp="PG-EAI-T2",
        evidence={"verified": True},
        root=object(),
        owner_id="production-smoke",
        authorized=True,
        evidence_verified=True,
        trinity_proof={
            "trust": True,
            "transparency": True,
            "performance": True,
        },
    )
    assert released["replayed"] is False

    with runtime._session_factory() as session:
        escrow = session.get(CanonicalEscrow, "PG-EAI-ESCROW")
        source = session.get(LedgerAccountModel, "PG-EAI-SOURCE")
        escrow_account = session.get(LedgerAccountModel, "PG-EAI-ESCROW")
        beneficiary = session.get(LedgerAccountModel, "PG-EAI-BENEFICIARY")

        assert escrow is not None and escrow.state == EscrowState.RELEASED.value
        assert source is not None and source.balance == 900
        assert escrow_account is not None and escrow_account.balance == 0
        assert beneficiary is not None and beneficiary.balance == 100
        assert session.query(LedgerMovementModel).count() == 2
        assert session.query(TransactionWitness).count() == 3
        assert session.query(OutboxEvent).count() == 3
        assert session.query(DurableIdempotencyRecord).count() == 3

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()
