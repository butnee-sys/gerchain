import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel, PostgreSQLAtomicLedger
from persistence.escrow_aggregate import EscrowBase, CanonicalEscrow, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.durable_idempotency import IdempotencyBase, DurableIdempotencyRecord
from persistence.atomic_value_transaction import WitnessBase, TransactionWitness
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth


def test_postgresql_canonical_value_flow():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, future=True)
    for base in (AtomicLedgerBase, EscrowBase, OutboxBase, IdempotencyBase, WitnessBase):
        base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    with Session() as session:
        session.add_all([
            LedgerAccountModel(account_id="SRC", currency="USD", balance=100, version=0, updated_at=now),
            LedgerAccountModel(account_id="BEN", currency="USD", balance=0, version=0, updated_at=now),
            LedgerAccountModel(account_id="esc-prod", currency="USD", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="esc-prod",
                sender_address="SRC",
                receiver_address="BEN",
                amount=40,
                state=EscrowState.CREATED.value,
                condition_desc="production smoke",
                refund_destination="SRC",
                currency="USD",
                version=0,
                created_at=now,
                updated_at=now,
            ),
        ])
        session.commit()

        fund_escrow_in_transaction(
            session, transaction_id="prod-fund-1", escrow_id="esc-prod",
            source="SRC", amount=40, currency="USD",
        )
        session.commit()

        lock_escrow_in_transaction(
            session, transaction_id="prod-lock-1", escrow_id="esc-prod",
        )
        session.commit()

        release_escrow_in_transaction(
            session, transaction_id="prod-release-1", escrow_id="esc-prod",
            beneficiary="BEN", amount=40, currency="USD",
            decision_status="APPROVE", authorization_status="AUTHORIZED",
            trust=True, transparency=True, performance=True,
            evidence_verified=True,
        )
        session.commit()

        escrow = session.get(CanonicalEscrow, "esc-prod")
        src = session.get(LedgerAccountModel, "SRC")
        ben = session.get(LedgerAccountModel, "BEN")
        movement = session.execute(select(LedgerMovementModel)).scalars().all()
        witnesses = session.execute(select(TransactionWitness)).scalars().all()
        outbox = session.execute(select(OutboxEvent)).scalars().all()
        idem = session.execute(select(DurableIdempotencyRecord)).scalars().all()

        assert escrow.state == EscrowState.RELEASED.value
        assert int(src.balance) == 60
        assert int(ben.balance) == 40
        assert len(movement) == 2
        assert len(witnesses) == 3
        assert len(outbox) == 3
        assert len(idem) == 3

        report = deep_reconcile_value_truth(session)
        assert report.matched, [f"{i.code}:{i.transaction_id}:{i.detail}" for i in report.issues]

    engine.dispose()

# PostgreSQL production evidence gate: exercised by GitHub Actions.
