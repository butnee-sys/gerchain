from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import DurableIdempotencyRecord
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.recovery_outbox import OutboxEvent
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


@pytest.mark.integration
def test_postgresql_production_runtime_full_value_path():
    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_DATABASE_URL is not configured")

    engine = create_engine(database_url, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="it-escrow",
            amount=40,
            currency="MNT",
            witness_id="it-witness",
        ),
        engine=engine,
    ).create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    now = datetime.now(timezone.utc)
    with session_factory.begin() as session:
        for table in (
            "gerchain_transaction_witnesses",
            "gerchain_outbox_events",
            "gerchain_idempotency_records",
            "gerchain_ledger_movements",
            "gerchain_ledger_accounts",
            "escrows",
        ):
            session.execute(text(f"DELETE FROM {table}"))
        session.add_all([
            LedgerAccountModel(account_id="IT-SRC", currency="MNT", balance=100, version=0, updated_at=now),
            LedgerAccountModel(account_id="it-escrow", currency="MNT", balance=0, version=0, updated_at=now),
            LedgerAccountModel(account_id="IT-BEN", currency="MNT", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="it-escrow",
                sender_address="IT-SRC",
                receiver_address="IT-BEN",
                amount=40,
                state=EscrowState.CREATED.value,
                condition_desc="integration",
                refund_destination="IT-SRC",
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            ),
        ])

    assert runtime.fund("it-fund", "IT-SRC", "T1", {"verified": True})["replayed"] is False
    assert runtime.lock("it-lock", "T2", {"verified": True})["replayed"] is False
    assert runtime.release(
        transaction_id="it-release",
        destination="IT-BEN",
        timestamp="T3",
        evidence={"verified": True},
        root=object(),
        owner_id="integration",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )["replayed"] is False

    with session_factory() as session:
        assert session.get(LedgerAccountModel, "IT-SRC").balance == 60
        assert session.get(LedgerAccountModel, "it-escrow").balance == 0
        assert session.get(LedgerAccountModel, "IT-BEN").balance == 40
        assert session.get(CanonicalEscrow, "it-escrow").state == "RELEASED"
        assert session.query(LedgerMovementModel).count() == 2
        assert session.query(TransactionWitness).count() == 3
        assert session.query(OutboxEvent).count() == 3
        assert session.query(DurableIdempotencyRecord).count() == 3
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()
