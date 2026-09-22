import os
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel, PostgreSQLAtomicLedger
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.atomic_value_transaction import TransactionWitness
from persistence.recovery_outbox import OutboxEvent
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_runtime_full_fund_lock_release_graph():
    database_url = os.environ["GERCHAIN_DATABASE_URL"]
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="integration-escrow",
            amount=100,
            currency="USD",
            witness_id="integration-witness",
        )
    )
    engine = factory.engine
    try:
        runtime = factory.create()
        assert runtime.is_canonical_ledger_authoritative

        Session = sessionmaker(bind=engine, expire_on_commit=False)
        now = datetime.now(timezone.utc)

        with Session() as session:
            PostgreSQLAtomicLedger.create_account_in_transaction(
                session, "integration-source", "USD", 100
            )
            PostgreSQLAtomicLedger.create_account_in_transaction(
                session, "integration-escrow", "USD", 0
            )
            PostgreSQLAtomicLedger.create_account_in_transaction(
                session, "integration-beneficiary", "USD", 0
            )
            session.add(
                CanonicalEscrow(
                    id="integration-escrow",
                    sender_address="integration-source",
                    receiver_address="integration-beneficiary",
                    amount=100,
                    state=EscrowState.CREATED.value,
                    condition_desc="integration",
                    refund_destination="integration-source",
                    currency="USD",
                    version=0,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.commit()

        with Session() as session:
            fund_escrow_in_transaction(
                session,
                transaction_id="integration-fund",
                escrow_id="integration-escrow",
                source="integration-source",
                amount=100,
                currency="USD",
            )
            session.commit()

        with Session() as session:
            lock_escrow_in_transaction(
                session,
                transaction_id="integration-lock",
                escrow_id="integration-escrow",
            )
            session.commit()

        with Session() as session:
            release_escrow_in_transaction(
                session,
                transaction_id="integration-release",
                escrow_id="integration-escrow",
                beneficiary="integration-beneficiary",
                amount=100,
                currency="USD",
                decision_status="APPROVE",
                authorization_status="AUTHORIZED",
                trust=True,
                transparency=True,
                performance=True,
                evidence_verified=True,
            )
            session.commit()

        with Session() as session:
            source = session.get(LedgerAccountModel, "integration-source")
            escrow = session.get(LedgerAccountModel, "integration-escrow")
            beneficiary = session.get(LedgerAccountModel, "integration-beneficiary")
            canonical_escrow = session.get(CanonicalEscrow, "integration-escrow")
            movement_count = session.scalar(select(func.count()).select_from(LedgerMovementModel))
            witness_count = session.scalar(select(func.count()).select_from(TransactionWitness))
            outbox_count = session.scalar(select(func.count()).select_from(OutboxEvent))
            report = deep_reconcile_value_truth(session)

            assert source.balance == 0
            assert escrow.balance == 0
            assert beneficiary.balance == 100
            assert canonical_escrow.state == EscrowState.RELEASED.value
            assert movement_count == 2
            assert witness_count == 3
            assert outbox_count == 3
            assert report.matched
    finally:
        engine.dispose()
