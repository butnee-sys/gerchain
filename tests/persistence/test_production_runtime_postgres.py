from datetime import datetime, timezone
import os

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, PostgreSQLAtomicLedger, AtomicLedgerBase
from persistence.atomic_value_transaction import TransactionWitness
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import DurableIdempotencyRecord
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState, EscrowBase
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_postgresql_boot_and_value_truth():
    # EA-35.16: branch-tip production PostgreSQL re-performance evidence.
    dsn = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(dsn, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=dsn,
            escrow_id="prod-esc-1",
            amount=100,
            currency="MNT",
            witness_id="prod-witness-1",
        ),
        engine=engine,
    ).create()
    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    with engine.connect() as connection:
        tables = {
            row[0]
            for row in connection.execute(
                text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'")
            )
        }
    assert {
        "schema_version",
        "escrows",
        "gerchain_ledger_accounts",
        "gerchain_ledger_movements",
        "gerchain_transaction_witnesses",
        "gerchain_outbox_events",
        "gerchain_idempotency_records",
    }.issubset(tables)

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
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    result = runtime.release(
        transaction_id="prod-release-1",
        destination="PROD-BEN",
        timestamp="T3",
        evidence={"test": True},
        root=object(),
        owner_id="prod-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )
    assert result["replayed"] is False
    replay = runtime.release(
        transaction_id="prod-release-1",
        destination="PROD-BEN",
        timestamp="T3",
        evidence={"test": True},
        root=object(),
        owner_id="prod-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )
    assert replay["replayed"] is True

    with session_factory() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    assert runtime.get_escrow_state()["state"] == "RELEASED"
    assert runtime.get_balance("PROD-BEN") == 100

    # REFUND: authoritative refund_destination must receive the value.
    now2 = datetime.now(timezone.utc)
    with session_factory() as session:
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "REFUND-SRC", "MNT", 100)
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "REFUND-BEN", "MNT", 0)
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "prod-refund-esc", "MNT", 0)
        session.add(CanonicalEscrow(id="prod-refund-esc", sender_address="REFUND-SRC", receiver_address="REFUND-BEN", amount=100, state=EscrowState.CREATED.value, condition_desc="refund-reperformance", refund_destination="REFUND-SRC", currency="MNT", version=0, created_at=now2, updated_at=now2))
        session.commit()
    refund_runtime = ProductionRuntimeFactory(ProductionRuntimeConfig(database_url=dsn, escrow_id="prod-refund-esc", amount=100, currency="MNT", witness_id="prod-refund-witness"), engine=engine).create()
    refund_runtime.fund("prod-refund-fund", "REFUND-SRC", "T4", {"test": True})
    refund_runtime.lock("prod-refund-lock", "T5", {"test": True})
    refund_result = refund_runtime.refund(transaction_id="prod-refund-1", destination="ATTACKER", timestamp="T6", evidence={"test": True}, root=object(), owner_id="prod-owner", authorized=True, evidence_verified=True, trinity_proof={"trust": True, "transparency": True, "performance": True})
    assert refund_result["replayed"] is False
    assert refund_runtime.get_escrow_state()["state"] == "REFUNDED"
    assert refund_runtime.get_balance("REFUND-SRC") == 100
    assert refund_runtime.get_balance("REFUND-BEN") == 0

    # CANCEL: FUNDED value returns to the authoritative original sender.
    now3 = datetime.now(timezone.utc)
    with session_factory() as session:
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "CANCEL-SRC", "MNT", 100)
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "CANCEL-BEN", "MNT", 0)
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "prod-cancel-esc", "MNT", 0)
        session.add(CanonicalEscrow(id="prod-cancel-esc", sender_address="CANCEL-SRC", receiver_address="CANCEL-BEN", amount=100, state=EscrowState.CREATED.value, condition_desc="cancel-reperformance", refund_destination="CANCEL-SRC", currency="MNT", version=0, created_at=now3, updated_at=now3))
        session.commit()
    cancel_runtime = ProductionRuntimeFactory(ProductionRuntimeConfig(database_url=dsn, escrow_id="prod-cancel-esc", amount=100, currency="MNT", witness_id="prod-cancel-witness"), engine=engine).create()
    cancel_runtime.fund("prod-cancel-fund", "CANCEL-SRC", "T7", {"test": True})
    cancel_result = cancel_runtime.cancel(transaction_id="prod-cancel-1", timestamp="T8", evidence={"test": True})
    assert cancel_result["replayed"] is False
    assert cancel_runtime.get_escrow_state()["state"] == "CANCELLED"
    assert cancel_runtime.get_balance("CANCEL-SRC") == 100
    assert cancel_runtime.get_balance("CANCEL-BEN") == 0

    # SETTLEMENT: direct movement remains a Canonical Ledger operation.
    with session_factory() as session:
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "SET-SRC", "MNT", 50)
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "SET-BEN", "MNT", 0)
        session.commit()
    settlement_runtime = ProductionRuntimeFactory(ProductionRuntimeConfig(database_url=dsn, escrow_id="prod-settlement-context", amount=1, currency="MNT", witness_id="prod-settlement-witness"), engine=engine).create()
    settlement_result = settlement_runtime.settle(transaction_id="prod-settlement-1", source="SET-SRC", destination="SET-BEN", amount=25, currency="MNT")
    assert settlement_result["replayed"] is False
    assert settlement_runtime.get_balance("SET-SRC") == 25
    assert settlement_runtime.get_balance("SET-BEN") == 25

    with session_factory() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()
