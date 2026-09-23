from datetime import datetime, timezone
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory
from persistence.atomic_ledger import LedgerAccountModel, AtomicLedgerBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.atomic_value_transaction import WitnessBase, TransactionWitness
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.durable_idempotency import IdempotencyBase, DurableIdempotencyRecord
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth


def test_production_postgres_runtime_full_value_flow():
    url = os.environ["TEST_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-smoke-escrow",
            amount=40,
            currency="MNT",
            witness_id="pg-smoke-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    now = datetime.now(timezone.utc)
    with factory.session_factory() as session:
        # Fresh CI database: the factory owns canonical persistence metadata.
        session.add_all([
            LedgerAccountModel(account_id="pg-source", currency="MNT", balance=100, version=0, updated_at=now),
            LedgerAccountModel(account_id="pg-beneficiary", currency="MNT", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="pg-smoke-escrow",
                sender_address="pg-source",
                receiver_address="pg-beneficiary",
                amount=40,
                state=EscrowState.CREATED.value,
                condition_desc="production smoke test",
                refund_destination="pg-source",
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            ),
        ])
        session.commit()

        fund_escrow_in_transaction(
            session,
            transaction_id="pg-fund-1",
            escrow_id="pg-smoke-escrow",
            source="pg-source",
            amount=40,
            currency="MNT",
        )
        session.commit()

        lock_escrow_in_transaction(
            session,
            transaction_id="pg-lock-1",
            escrow_id="pg-smoke-escrow",
        )
        session.commit()

        release_escrow_in_transaction(
            session,
            transaction_id="pg-release-1",
            escrow_id="pg-smoke-escrow",
            beneficiary="pg-beneficiary",
            amount=40,
            currency="MNT",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        session.commit()

        source = session.get(LedgerAccountModel, "pg-source")
        beneficiary = session.get(LedgerAccountModel, "pg-beneficiary")
        escrow = session.get(CanonicalEscrow, "pg-smoke-escrow")
        assert source.balance == 60
        assert beneficiary.balance == 40
        assert escrow.state == EscrowState.RELEASED.value

        report = deep_reconcile_value_truth(session)
        assert report.matched, [f"{i.code}: {i.detail}" for i in report.issues]

    engine.dispose()
