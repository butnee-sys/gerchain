import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel, PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import WitnessBase, TransactionWitness
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase, CanonicalEscrow, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory
from persistence.cancel_escrow import cancel_escrow_in_transaction
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.settlement_coordinator import SettlementCoordinator
from persistence.deep_value_reconciliation import deep_reconcile_value_truth


@pytest.mark.postgres
def test_production_postgres_factory_and_canonical_value_flow():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-smoke-escrow",
            amount=100,
            currency="MNT",
            witness_id="pg-smoke-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    for base in (AtomicLedgerBase, EscrowBase, OutboxBase, IdempotencyBase, WitnessBase):
        base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)
    with Session() as session:
        accounts = [
            ("pg-fund-source", 100), ("pg-release-escrow", 0), ("pg-release-beneficiary", 0),
            ("pg-refund-source", 100), ("pg-refund-escrow", 0),
            ("pg-cancel-source", 75), ("pg-cancel-escrow", 0),
            ("pg-settle-source", 50), ("pg-settle-destination", 0),
        ]
        for account_id, balance in accounts:
            session.add(LedgerAccountModel(account_id=account_id, currency="MNT", balance=balance, version=0, updated_at=now))
        session.add_all([
            CanonicalEscrow(id="pg-release-escrow", sender_address="pg-fund-source", receiver_address="pg-release-beneficiary", refund_destination="pg-fund-source", amount=100, state=EscrowState.CREATED.value, condition_desc="postgres-release", currency="MNT", version=0, created_at=now, updated_at=now),
            CanonicalEscrow(id="pg-refund-escrow", sender_address="pg-refund-source", receiver_address="pg-refund-source", refund_destination="pg-refund-source", amount=100, state=EscrowState.CREATED.value, condition_desc="postgres-refund", currency="MNT", version=0, created_at=now, updated_at=now),
            CanonicalEscrow(id="pg-cancel-escrow", sender_address="pg-cancel-source", receiver_address="pg-cancel-source", refund_destination="pg-cancel-source", amount=75, state=EscrowState.CREATED.value, condition_desc="postgres-cancel", currency="MNT", version=0, created_at=now, updated_at=now),
        ])
        session.commit()

        fund_escrow_in_transaction(session, transaction_id="pg-fund-tx", escrow_id="pg-release-escrow", source="pg-fund-source", amount=100, currency="MNT")
        lock_escrow_in_transaction(session, transaction_id="pg-lock-tx", escrow_id="pg-release-escrow")
        release_escrow_in_transaction(session, transaction_id="pg-release-tx", escrow_id="pg-release-escrow", beneficiary="pg-release-beneficiary", amount=100, currency="MNT", decision_status="APPROVE", authorization_status="AUTHORIZED", trust=True, transparency=True, performance=True, evidence_verified=True)

        fund_escrow_in_transaction(session, transaction_id="pg-refund-fund-tx", escrow_id="pg-refund-escrow", source="pg-refund-source", amount=100, currency="MNT")
        lock_escrow_in_transaction(session, transaction_id="pg-refund-lock-tx", escrow_id="pg-refund-escrow")
        refund_escrow_in_transaction(session, transaction_id="pg-refund-tx", escrow_id="pg-refund-escrow", amount=100, currency="MNT")

        fund_escrow_in_transaction(session, transaction_id="pg-cancel-fund-tx", escrow_id="pg-cancel-escrow", source="pg-cancel-source", amount=75, currency="MNT")
        cancel_escrow_in_transaction(session, transaction_id="pg-cancel-tx", escrow_id="pg-cancel-escrow")

        SettlementCoordinator(session).settle_in_transaction(transaction_id="pg-settlement-tx", source="pg-settle-source", destination="pg-settle-destination", amount=25, currency="MNT")
        session.commit()

        escrows = {row.id: row.state for row in session.execute(select(CanonicalEscrow).where(CanonicalEscrow.id.in_(["pg-release-escrow", "pg-refund-escrow", "pg-cancel-escrow"]))).scalars()}
        balances = {row.account_id: row.balance for row in session.execute(select(LedgerAccountModel)).scalars() if row.account_id.startswith("pg-")}
        movements = session.execute(select(LedgerMovementModel)).scalars().all()
        witnesses = session.execute(select(TransactionWitness)).scalars().all()
        outbox = session.execute(select(OutboxEvent)).scalars().all()
        report = deep_reconcile_value_truth(session)

        assert escrows == {"pg-release-escrow": EscrowState.RELEASED.value, "pg-refund-escrow": EscrowState.REFUNDED.value, "pg-cancel-escrow": EscrowState.CANCELLED.value}
        assert balances["pg-fund-source"] == 0
        assert balances["pg-release-beneficiary"] == 100
        assert balances["pg-refund-source"] == 100
        assert balances["pg-cancel-source"] == 75
        assert balances["pg-settle-source"] == 25
        assert balances["pg-settle-destination"] == 25
        assert len(movements) == 6
        assert {m.operation for m in movements} == {"FUND", "RELEASE", "REFUND", "CANCEL", "SETTLEMENT"}
        assert {w.event_type for w in witnesses} >= {"GERCHAIN_FUNDED", "GERCHAIN_LOCKED", "GERCHAIN_RELEASED", "GERCHAIN_REFUNDED", "GERCHAIN_CANCELLED", "GERCHAIN_SETTLED"}
        assert {e.event_type for e in outbox} >= {"GERCHAIN_FUNDED", "GERCHAIN_LOCKED", "GERCHAIN_RELEASED", "GERCHAIN_REFUNDED", "GERCHAIN_CANCELLED", "GERCHAIN_SETTLED"}
        assert report.matched, report.issues
        assert report.canonical_movement_count == 6

    engine.dispose()
