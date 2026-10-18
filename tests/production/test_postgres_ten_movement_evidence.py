from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import (
    AtomicLedgerBase,
    LedgerAccountModel,
    PostgreSQLAtomicLedger,
)
from persistence.atomic_value_transaction import AtomicValueTransaction, WitnessBase
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.recovery_outbox import OutboxBase
from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)


@pytest.mark.postgres
def test_ten_real_postgres_movements_have_complete_evidence_graph():
    """Create ten canonical Ledger movements and prove every evidence edge on PostgreSQL."""
    database_url = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is not configured")

    engine = create_engine(database_url, pool_pre_ping=True, future=True)
    try:
        factory = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=database_url,
                escrow_id="ten-movement-bootstrap",
                amount=1,
                currency="MNT",
                witness_id="ten-movement-witness",
            ),
            engine=engine,
        )
        runtime = factory.create()
        assert runtime.is_canonical_ledger_authoritative

        with engine.begin() as connection:
            connection.execute(text(
                "TRUNCATE TABLE gerchain_ledger_movements, gerchain_ledger_accounts, "
                "escrows, gerchain_transaction_witnesses, gerchain_outbox_events, "
                "gerchain_idempotency_records RESTART IDENTITY CASCADE"
            ))

        session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        now = datetime.now(timezone.utc)
        with session_factory() as session:
            ledger = PostgreSQLAtomicLedger(session_factory)
            for i in range(10):
                escrow_id = f"evidence-escrow-{i:02d}"
                source = f"evidence-source-{i:02d}"
                destination = f"evidence-beneficiary-{i:02d}"
                ledger.create_account_in_transaction(session, source, "MNT", 100)
                # Seed the locked escrow with the value being released; this
                # evidence-only fixture does not exercise the FUND movement.
                ledger.create_account_in_transaction(session, escrow_id, "MNT", 10)
                ledger.create_account_in_transaction(session, destination, "MNT", 0)
                session.add(CanonicalEscrow(
                    id=escrow_id,
                    sender_address=source,
                    receiver_address=destination,
                    amount=10,
                    state=EscrowState.LOCKED.value,
                    condition_desc="postgres evidence graph test",
                    refund_destination=source,
                    currency="MNT",
                    version=2,
                    created_at=now,
                    updated_at=now,
                ))
            session.commit()

        with session_factory() as session:
            ledger = PostgreSQLAtomicLedger(session_factory)
            for i in range(10):
                escrow_id = f"evidence-escrow-{i:02d}"
                source = escrow_id
                destination = f"evidence-beneficiary-{i:02d}"
                transaction_id = f"evidence-release-{i:02d}"
                AtomicValueTransaction(session).transfer_and_transition(
                    transaction_id=transaction_id,
                    escrow_id=escrow_id,
                    source=source,
                    destination=destination,
                    amount=10,
                    currency="MNT",
                    expected_state=EscrowState.LOCKED,
                    new_state=EscrowState.RELEASED,
                    ledger_transfer=ledger.transfer_in_transaction,
                    event_type="GERCHAIN_RELEASED",
                    payload={"test": "ten-movement-evidence"},
                )
            session.commit()

        with session_factory() as session:
            report = deep_reconcile_value_truth(session)
            assert report.matched, [issue.__dict__ for issue in report.issues]
            assert report.canonical_movement_count == 10
            assert report.witness_count == 10
            assert report.outbox_count == 10
            assert report.idempotency_count == 10
            assert report.escrow_count == 10
            rows = session.query(LedgerAccountModel).all()
            balances = {row.account_id: row.balance for row in rows}
            for i in range(10):
                assert balances[f"evidence-source-{i:02d}"] == 100
                assert balances[f"evidence-escrow-{i:02d}"] == 0
                assert balances[f"evidence-beneficiary-{i:02d}"] == 10
    finally:
        engine.dispose()
