import os
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import create_engine, select

from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.recovery_outbox import OutboxEvent
from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)


def test_production_postgres_factory_and_value_flow():
    dsn = os.environ["GERCHAIN_POSTGRES_DSN"]
    engine = create_engine(dsn, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=dsn,
            escrow_id="eai-pg-smoke",
            amount=40,
            currency="MNT",
            witness_id="w-pg-smoke",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    now = datetime.now(timezone.utc)
    with factory.session_factory.begin() as session:
        session.add_all(
            [
                LedgerAccountModel(account_id="SRC", currency="MNT", balance=100, version=0, updated_at=now),
                LedgerAccountModel(account_id="eai-pg-smoke", currency="MNT", balance=0, version=0, updated_at=now),
                LedgerAccountModel(account_id="BEN", currency="MNT", balance=0, version=0, updated_at=now),
                CanonicalEscrow(
                    id="eai-pg-smoke",
                    sender_address="SRC",
                    receiver_address="BEN",
                    amount=40,
                    state=EscrowState.CREATED.value,
                    condition_desc="production-postgres-smoke",
                    refund_destination="SRC",
                    currency="MNT",
                    version=0,
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )

    with factory.session_factory.begin() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="pg-fund-1",
            escrow_id="eai-pg-smoke",
            source="SRC",
            amount=40,
            currency="MNT",
        )

    with factory.session_factory.begin() as session:
        lock_escrow_in_transaction(
            session,
            transaction_id="pg-lock-1",
            escrow_id="eai-pg-smoke",
        )

    with factory.session_factory.begin() as session:
        release_escrow_in_transaction(
            session,
            transaction_id="pg-release-1",
            escrow_id="eai-pg-smoke",
            beneficiary="BEN",
            amount=40,
            currency="MNT",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )

    with factory.session_factory() as session:
        src = session.get(LedgerAccountModel, "SRC")
        escrow = session.get(LedgerAccountModel, "eai-pg-smoke")
        ben = session.get(LedgerAccountModel, "BEN")
        durable_escrow = session.get(CanonicalEscrow, "eai-pg-smoke")
        assert src.balance == Decimal("60")
        assert escrow.balance == Decimal("0")
        assert ben.balance == Decimal("40")
        assert durable_escrow.state == EscrowState.RELEASED.value
        assert session.query(LedgerMovementModel).count() == 2
        assert session.query(TransactionWitness).count() == 3
        assert session.query(OutboxEvent).count() == 3
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()
