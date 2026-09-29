from datetime import datetime, timezone

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import DurableIdempotencyRecord, IdempotencyBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.recovery_outbox import OutboxBase
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker


def _factory():
    import os

    url = os.environ["GERCHAIN_POSTGRES_DSN"]
    engine = create_engine(url, future=True)
    for base in (AtomicLedgerBase, EscrowBase, WitnessBase, OutboxBase, IdempotencyBase):
        base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def test_canonical_postgres_transaction_and_deep_truth():
    engine, factory = _factory()
    now = datetime.now(timezone.utc)

    with factory() as session:
        ledger = PostgreSQLAtomicLedger(factory)
        ledger.create_account_in_transaction(session, "SRC", "USD", 60)
        ledger.create_account_in_transaction(session, "escrow-1", "USD", 40)
        ledger.create_account_in_transaction(session, "BENEFICIARY", "USD", 0)

        session.add(
            CanonicalEscrow(
                id="escrow-1",
                sender_address="SRC",
                receiver_address="BENEFICIARY",
                refund_destination="SRC",
                amount=40,
                state=EscrowState.LOCKED.value,
                condition_desc="postgres canonical gate",
                currency="USD",
                version=2,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

        from persistence.release_escrow import release_escrow_in_transaction

        result = release_escrow_in_transaction(
            session,
            transaction_id="pg-release-1",
            escrow_id="escrow-1",
            beneficiary="BENEFICIARY",
            amount=40,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
            payload={"gate": "EA-35.13"},
        )
        session.commit()

        assert result["replayed"] is False
        assert session.execute(
            select(LedgerAccountModel).where(LedgerAccountModel.account_id == "SRC")
        ).scalar_one().balance == 60
        assert session.execute(
            select(LedgerAccountModel).where(
                LedgerAccountModel.account_id == "BENEFICIARY"
            )
        ).scalar_one().balance == 40

        report = deep_reconcile_value_truth(session)
        assert report.matched, [f"{i.code}: {i.detail}" for i in report.issues]

        movement = session.execute(
            select(LedgerAccountModel).where(LedgerAccountModel.account_id == "escrow-1")
        ).scalar_one()
        assert movement.balance == 0

    engine.dispose()
