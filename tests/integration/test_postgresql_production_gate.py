from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from persistence.escrow_aggregate import CanonicalEscrow
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from sqlalchemy import create_engine, text\n\nfrom services.gerchain_runtime_factory import ProductionRuntimeFactory

DATABASE_URL = os.environ.get("GERCHAIN_TEST_DATABASE_URL")


@pytest.mark.integration
def test_real_postgresql_production_boot_and_value_flow():
    if not DATABASE_URL:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required")

    config = ProductionRuntimeConfig(
        database_url=DATABASE_URL,
        escrow_id="pg-ea35-escrow",
        amount=25,
        currency="MNT",
        witness_id="pg-ea35-witness",
    )
    factory = ProductionRuntimeFactory(config)
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    # Second construction proves migration idempotency.
    factory.create()

    now = datetime.now(timezone.utc)
    with factory.session_factory() as session:
        for table in (
            "gerchain_ledger_movements",
            "gerchain_transaction_witnesses",
            "gerchain_outbox_events",
            "gerchain_idempotency_records",
            "gerchain_ledger_accounts",
            "escrows",
        ):
            session.execute(text(f"DELETE FROM {table}"))
        session.add(CanonicalEscrow(
            id="pg-ea35-escrow",
            sender_address="SRC",
            receiver_address="BEN",
            amount=25,
            state="CREATED",
            condition_desc="production integration",
            refund_destination="SRC",
            currency="MNT",
            version=0,
            created_at=now,
            updated_at=now,
        ))
        session.commit()

    runtime.create_account("SRC", initial_balance=100)
    runtime.create_account("BEN", initial_balance=0)
    runtime.fund("pg-fund", "SRC", now.isoformat(), {"integration": True})
    runtime.lock("pg-lock", now.isoformat(), {"integration": True})
    runtime.release(
        transaction_id="pg-release",
        destination="BEN",
        timestamp=now.isoformat(),
        evidence={"integration": True},
        root=object(),
        owner_id="integration-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )

    assert runtime.get_balance("SRC") == 75
    assert runtime.get_balance("BEN") == 25
    assert runtime.get_escrow_state()["state"] == "RELEASED"

    with factory.session_factory() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, [issue.__dict__ for issue in report.issues]
        assert report.canonical_movement_count == 2
        assert report.witness_count == 3
        assert report.outbox_count == 3
        assert session.execute(text("SELECT MAX(version) FROM schema_version")).scalar_one() == 11
