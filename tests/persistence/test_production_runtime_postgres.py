from datetime import datetime, timezone
import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, PostgreSQLAtomicLedger, AtomicLedgerBase
from persistence.atomic_value_transaction import TransactionWitness
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import DurableIdempotencyRecord
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState, EscrowBase
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_postgresql_boot_and_value_truth():
    dsn = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(dsn, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    runtime = ProductionRuntimeFactory.create(
        escrow_id="prod-esc-1",
        amount=100,
        currency="MNT",
        witness_id="prod-witness-1",
        engine=engine,
        session_factory=session_factory,
    ).create()
    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    now = datetime.now(timezone.utc)
    with session_factory() as session:
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "PROD-SRC", "MNT", 100)
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "PROD-BEN", "MNT", 0)
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "prod-esc-1", "MNT", 0)
        session.add(CanonicalEscrow(
            id="prod-esc-1",
            sender_address="PROD-SRC",
            receiver_address="PROD-BEN",
            amount=100,
            state=EscrowState.CREATED.value,
            condition_desc="production-reperformance",
            refund_destination="PROD-SRC",
            currency="MNT",
            version=0,
            created_at=now,
            updated_at=now,
        ))
        session.commit()

    assert runtime.get_escrow_state()["state"] == "CREATED"
    runtime.fund("prod-fund-1", "PROD-SRC", "T1", {"test": True})
    runtime.lock("prod-lock-1", "T2", {"test": True})

    assert runtime.get_escrow_state()["state"] == "LOCKED"
    assert runtime.get_balance("PROD-SRC") == 0
    assert runtime.get_balance("prod-esc-1") == 100

    with session_factory() as session:
        from persistence.release_escrow import release_escrow_in_transaction
        result = release_escrow_in_transaction(
            session,
            transaction_id="prod-release-1",
            escrow_id="prod-esc-1",
            beneficiary="PROD-BEN",
            amount=100,
            currency="MNT",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
            payload={"test": True},
        )
        session.commit()
        assert result["replayed"] is False

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    assert runtime.get_escrow_state()["state"] == "RELEASED"
    assert runtime.get_balance("PROD-BEN") == 100

    engine.dispose()
