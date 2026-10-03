from __future__ import annotations

import os

from sqlalchemy import func, select

from persistence.atomic_ledger import LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import DurableIdempotencyRecord
from persistence.escrow_aggregate import CanonicalEscrow
from persistence.recovery_outbox import OutboxEvent
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_postgresql_full_value_flow() -> None:
    database_url = os.environ["GERCHAIN_DATABASE_URL"]
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="pg-eai-bootstrap",
            amount=1,
            currency="MNT",
            witness_id="pg-eai-witness",
        )
    )
    runtime = factory.create()

    for account, balance in (
        ("pg-source", 1000),
        ("pg-beneficiary", 0),
        ("pg-refund", 80),
        ("pg-cancel", 60),
        ("pg-settlement-source", 200),
        ("pg-settlement-dest", 0),
        ("pg-release-escrow", 0),
        ("pg-refund-escrow", 0),
        ("pg-cancel-escrow", 0),
    ):
        runtime.create_account(account, balance)

    release_runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="pg-release-escrow",
            amount=100,
            currency="MNT",
            witness_id="pg-release-witness",
        )
    ).create()
    release_runtime.create_escrow(
        escrow_id="pg-release-escrow",
        source="pg-source",
        beneficiary="pg-beneficiary",
        refund_destination="pg-source",
        amount=100,
        currency="MNT",
    )
    release_runtime.fund("pg-fund-1", "pg-source", "T1", {"test": "postgres"})
    release_runtime.lock("pg-lock-1", "T2", {"test": "postgres"})
    release_runtime.release(
        transaction_id="pg-release-1",
        destination="pg-beneficiary",
        timestamp="T3",
        evidence={"test": "postgres"},
        root=object(),
        owner_id="pg-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )

    refund_runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="pg-refund-escrow",
            amount=80,
            currency="MNT",
            witness_id="pg-refund-witness",
        )
    ).create()
    refund_runtime.create_escrow(
        escrow_id="pg-refund-escrow",
        source="pg-refund",
        beneficiary="pg-beneficiary",
        refund_destination="pg-refund",
        amount=80,
        currency="MNT",
    )
    refund_runtime.fund("pg-fund-2", "pg-refund", "T4", {"test": "postgres"})
    refund_runtime.lock("pg-lock-2", "T5", {"test": "postgres"})
    refund_runtime.refund(
        transaction_id="pg-refund-1",
        destination="pg-attacker",
        timestamp="T6",
        evidence={"test": "postgres"},
        root=object(),
        owner_id="pg-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )

    cancel_runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="pg-cancel-escrow",
            amount=60,
            currency="MNT",
            witness_id="pg-cancel-witness",
        )
    ).create()
    cancel_runtime.create_escrow(
        escrow_id="pg-cancel-escrow",
        source="pg-cancel",
        beneficiary="pg-beneficiary",
        refund_destination="pg-cancel",
        amount=60,
        currency="MNT",
    )
    cancel_runtime.fund("pg-fund-3", "pg-cancel", "T7", {"test": "postgres"})
    cancel_runtime.cancel(
        transaction_id="pg-cancel-1",
        timestamp="T8",
        evidence={"test": "postgres"},
    )

    runtime.settle(
        transaction_id="pg-settlement-1",
        source="pg-settlement-source",
        destination="pg-settlement-dest",
        amount=75,
        currency="MNT",
    )

    assert runtime.get_balance("pg-source") == 900
    assert runtime.get_balance("pg-beneficiary") == 100
    assert runtime.get_balance("pg-refund") == 80
    assert runtime.get_balance("pg-cancel") == 60
    assert runtime.get_balance("pg-settlement-source") == 125
    assert runtime.get_balance("pg-settlement-dest") == 75

    with factory.session_factory() as session:
        assert session.execute(
            select(CanonicalEscrow.state).where(CanonicalEscrow.id == "pg-release-escrow")
        ).scalar_one() == "RELEASED"
        assert session.execute(
            select(CanonicalEscrow.state).where(CanonicalEscrow.id == "pg-refund-escrow")
        ).scalar_one() == "REFUNDED"
        assert session.execute(
            select(CanonicalEscrow.state).where(CanonicalEscrow.id == "pg-cancel-escrow")
        ).scalar_one() == "CANCELLED"

        assert session.execute(select(func.count()).select_from(LedgerMovementModel)).scalar_one() == 7
        assert session.execute(select(func.count()).select_from(TransactionWitness)).scalar_one() == 9
        assert session.execute(select(func.count()).select_from(OutboxEvent)).scalar_one() == 9
        assert session.execute(select(func.count()).select_from(DurableIdempotencyRecord)).scalar_one() == 9

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues
