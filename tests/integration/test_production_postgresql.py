from datetime import datetime, timezone
import os

from sqlalchemy import select

from persistence.atomic_ledger import LedgerAccountModel, PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import TransactionWitness
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import DurableIdempotencyRecord
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.transactional_outbox import OutboxEvent
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_postgresql_full_value_flow():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-proof-escrow",
            amount=100,
            currency="USD",
            witness_id="pg-proof-witness",
        )
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    with factory.session_factory() as session:
        session.query(DurableIdempotencyRecord).delete()
        session.query(TransactionWitness).delete()
        session.query(OutboxEvent).delete()
        session.query(LedgerAccountModel).delete()
        session.query(CanonicalEscrow).delete()
        session.commit()

        now = datetime.now(timezone.utc)
        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, "pg-proof-source", "USD", 1000
        )
        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, "pg-proof-escrow", "USD", 0
        )
        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, "pg-proof-dest", "USD", 0
        )
        session.add(CanonicalEscrow(
            id="pg-proof-escrow",
            sender_address="pg-proof-source",
            receiver_address="pg-proof-dest",
            amount=100,
            state=EscrowState.CREATED.value,
            condition_desc="production-postgresql-reperformance",
            refund_destination="pg-proof-source",
            currency="USD",
            version=0,
            created_at=now,
            updated_at=now,
        ))
        session.commit()

        fund_escrow_in_transaction(
            session,
            transaction_id="pg-proof-fund",
            escrow_id="pg-proof-escrow",
            source="pg-proof-source",
            amount=100,
            currency="USD",
        )
        session.commit()

        lock_escrow_in_transaction(
            session,
            transaction_id="pg-proof-lock",
            escrow_id="pg-proof-escrow",
        )
        session.commit()

        release_escrow_in_transaction(
            session,
            transaction_id="pg-proof-release",
            escrow_id="pg-proof-escrow",
            beneficiary="pg-proof-dest",
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

        balances = {
            row.account_id: row.balance
            for row in session.execute(select(LedgerAccountModel)).scalars()
        }
        assert balances == {
            "pg-proof-source": 900,
            "pg-proof-escrow": 0,
            "pg-proof-dest": 100,
        }

        escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == "pg-proof-escrow")
        ).scalar_one()
        assert escrow.state == EscrowState.RELEASED.value

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues
        assert session.query(TransactionWitness).count() == 3
        assert session.query(OutboxEvent).count() == 3
        assert session.query(DurableIdempotencyRecord).count() == 3
