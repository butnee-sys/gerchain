from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow
from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)

DATABASE_URL = os.environ.get("GERCHAIN_TEST_DATABASE_URL")


@pytest.mark.integration
def test_real_postgresql_production_boot_and_value_flow():
    if not DATABASE_URL:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required")

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    config = ProductionRuntimeConfig(
        database_url=DATABASE_URL,
        escrow_id="pg-ea35-escrow",
        amount=25,
        currency="MNT",
        witness_id="pg-ea35-witness",
    )
    factory = ProductionRuntimeFactory(config, engine=engine)
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    now = datetime.now(timezone.utc)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_factory() as session:
        for table in (
            "gerchain_ledger_movements",
            "gerchain_transaction_witnesses",
            "gerchain_outbox_events",
            "gerchain_idempotency_records",
            "gerchain_ledger_accounts",
            "escrows",
        ):
            session.execute(text(f"DELETE FROM {table}"))
        session.add(
            CanonicalEscrow(
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
            )
        )
        session.commit()

    runtime.create_account("SRC", initial_balance=100)
    runtime.create_account("BEN", initial_balance=0)
    # FUND moves source -> the canonical escrow ledger account; provision it explicitly.
    runtime.create_account("pg-ea35-escrow", initial_balance=0)
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
        trinity_proof={
            "trust": True,
            "transparency": True,
            "performance": True,
        },
    )

    assert runtime.get_balance("SRC") == 75
    assert runtime.get_balance("BEN") == 25
    assert runtime.get_escrow_state()["state"] == "RELEASED"

    with session_factory() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, [issue.__dict__ for issue in report.issues]
        assert report.canonical_movement_count == 2
        assert report.witness_count == 3
        assert report.outbox_count == 3

    engine.dispose()


@pytest.mark.integration
def test_real_postgresql_full_value_lifecycle_and_settlement():
    if not DATABASE_URL:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required")

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    base_ids = (
        "gerchain_ledger_movements",
        "gerchain_transaction_witnesses",
        "gerchain_outbox_events",
        "gerchain_idempotency_records",
        "gerchain_ledger_accounts",
        "escrows",
    )
    with sessions.begin() as session:
        for table in base_ids:
            session.execute(text(f"DELETE FROM {table}"))

    def make_runtime(escrow_id: str, amount: int):
        return ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=DATABASE_URL,
                escrow_id=escrow_id,
                amount=amount,
                currency="MNT",
                witness_id=f"witness-{escrow_id}",
            ),
            engine=engine,
        ).create()

    release_rt = make_runtime("full-release", 25)
    refund_rt = make_runtime("full-refund", 15)
    cancel_rt = make_runtime("full-cancel", 10)
    settlement_rt = make_runtime("full-settlement", 1)

    with sessions.begin() as session:
        session.add_all([
            CanonicalEscrow(
                id="full-release", sender_address="SRC-R", receiver_address="BEN-R",
                refund_destination="SRC-R", amount=25, state="CREATED",
                condition_desc="release", currency="MNT", version=0,
                created_at=now, updated_at=now,
            ),
            CanonicalEscrow(
                id="full-refund", sender_address="SRC-F", receiver_address="BEN-F",
                refund_destination="SRC-F", amount=15, state="CREATED",
                condition_desc="refund", currency="MNT", version=0,
                created_at=now, updated_at=now,
            ),
            CanonicalEscrow(
                id="full-cancel", sender_address="SRC-C", receiver_address="BEN-C",
                refund_destination="SRC-C", amount=10, state="CREATED",
                condition_desc="cancel", currency="MNT", version=0,
                created_at=now, updated_at=now,
            ),
        ])

    for account_id, balance in (
        ("SRC-R", 100), ("BEN-R", 0), ("full-release", 0),
        ("SRC-F", 100), ("BEN-F", 0), ("full-refund", 0),
        ("SRC-C", 100), ("BEN-C", 0), ("full-cancel", 0),
        ("SETTLE-SRC", 50), ("SETTLE-BEN", 0),
    ):
        settlement_rt.create_account(account_id, balance)

    release_rt.fund("full-fund-r", "SRC-R", now.isoformat(), {"case": "release"})
    release_rt.lock("full-lock-r", now.isoformat(), {"case": "release"})
    release_rt.release(
        transaction_id="full-release-r",
        destination="BEN-R",
        timestamp=now.isoformat(),
        evidence={"case": "release"},
        root=object(),
        owner_id="full-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )

    refund_rt.fund("full-fund-f", "SRC-F", now.isoformat(), {"case": "refund"})
    refund_rt.lock("full-lock-f", now.isoformat(), {"case": "refund"})
    refund_rt.refund(
        transaction_id="full-refund-f",
        destination="ATTACKER",
        timestamp=now.isoformat(),
        evidence={"case": "refund"},
        root=object(),
        owner_id="full-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )

    cancel_rt.fund("full-fund-c", "SRC-C", now.isoformat(), {"case": "cancel"})
    cancel_rt.cancel(
        transaction_id="full-cancel-c",
        timestamp=now.isoformat(),
        evidence={"case": "cancel"},
    )

    settlement_rt.settle(
        transaction_id="full-settlement-s",
        source="SETTLE-SRC",
        destination="SETTLE-BEN",
        amount=7,
        currency="MNT",
    )

    assert release_rt.get_balance("SRC-R") == 75
    assert release_rt.get_balance("BEN-R") == 25
    assert refund_rt.get_balance("SRC-F") == 100
    assert refund_rt.get_balance("full-refund") == 0
    assert cancel_rt.get_balance("SRC-C") == 100
    assert settlement_rt.get_balance("SETTLE-SRC") == 43
    assert settlement_rt.get_balance("SETTLE-BEN") == 7

    with sessions() as session:
        states = {
            row.id: row.state
            for row in session.execute(
                text("SELECT id, state FROM escrows ORDER BY id")
            ).mappings()
        }
        report = deep_reconcile_value_truth(session)

    assert states == {
        "full-cancel": "CANCELLED",
        "full-refund": "REFUNDED",
        "full-release": "RELEASED",
    }
    assert report.matched, [issue.__dict__ for issue in report.issues]
    assert report.canonical_movement_count == 7
    assert report.witness_count == 9
    assert report.outbox_count == 9

    engine.dispose()
