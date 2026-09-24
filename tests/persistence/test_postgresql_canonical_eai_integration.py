from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel, PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.durable_idempotency import IdempotencyBase, DurableIdempotencyRecord
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.deep_value_reconciliation import deep_reconcile_value_truth


def test_real_postgresql_canonical_eai_fund_lock_release_reconciles() -> None:
    dsn = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(dsn, pool_pre_ping=True)
    for base in (AtomicLedgerBase, EscrowBase, WitnessBase, IdempotencyBase, OutboxBase):
        base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    now = datetime.now(timezone.utc)
    with factory() as session:
        session.add_all([
            LedgerAccountModel(account_id="pg-source", currency="USD", balance=100, version=0, updated_at=now),
            LedgerAccountModel(account_id="pg-beneficiary", currency="USD", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="pg-escrow-1",
                sender_address="pg-source",
                receiver_address="pg-beneficiary",
                amount=40,
                state=EscrowState.CREATED.value,
                condition_desc="production integration",
                refund_destination="pg-source",
                currency="USD",
                version=0,
                created_at=now,
                updated_at=now,
            ),
        ])
        session.commit()

        fund_escrow_in_transaction(
            session,
            transaction_id="pg-fund-1",
            escrow_id="pg-escrow-1",
            source="pg-source",
            amount=40,
            currency="USD",
        )
        session.commit()

        lock_escrow_in_transaction(
            session,
            transaction_id="pg-lock-1",
            escrow_id="pg-escrow-1",
        )
        session.commit()

        release_escrow_in_transaction(
            session,
            transaction_id="pg-release-1",
            escrow_id="pg-escrow-1",
            beneficiary="pg-beneficiary",
            amount=40,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        session.commit()

        escrow = session.get(CanonicalEscrow, "pg-escrow-1")
        source = session.get(LedgerAccountModel, "pg-source")
        beneficiary = session.get(LedgerAccountModel, "pg-beneficiary")
        movements = session.execute(select(LedgerMovementModel)).scalars().all()
        witnesses = session.execute(select(TransactionWitness)).scalars().all()
        outboxes = session.execute(select(OutboxEvent)).scalars().all()
        idempotencies = session.execute(select(DurableIdempotencyRecord)).scalars().all()
        report = deep_reconcile_value_truth(session)

        assert escrow is not None and escrow.state == EscrowState.RELEASED.value
        assert source is not None and source.balance == 60
        assert beneficiary is not None and beneficiary.balance == 40
        assert len(movements) == 2
        assert len(witnesses) == 3
        assert len(outboxes) == 3
        assert len(idempotencies) == 3
        assert report.matched

    engine.dispose()
