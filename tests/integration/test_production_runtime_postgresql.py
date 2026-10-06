from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import sessionmaker

from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness
from persistence.recovery_outbox import OutboxEvent
from persistence.durable_idempotency import DurableIdempotencyRecord
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_runtime_boots_and_executes_canonical_postgresql_flow() -> None:
    database_url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(database_url, pool_pre_ping=True)
    # The production factory must own canonical migration application.
    runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="pg-e2e-escrow",
            amount=100,
            currency="USD",
            witness_id="pg-e2e-witness",
        ),
        engine=engine,
    ).create()
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    assert runtime.is_canonical_ledger_authoritative

    with engine.connect() as connection:
        migration_version = connection.execute(
            text("SELECT MAX(version) FROM schema_version")
        ).scalar_one()
    assert migration_version >= 11

    tables = set(inspect(engine).get_table_names())
    for table in (
        "escrows",
        "gerchain_ledger_accounts",
        "gerchain_ledger_movements",
        "gerchain_transaction_witnesses",
        "gerchain_outbox_events",
        "gerchain_idempotency_records",
    ):
        assert table in tables

    now = datetime.now(timezone.utc)
    with session_factory() as session:
        session.add(
            CanonicalEscrow(
                id="pg-e2e-escrow",
                sender_address="SRC",
                receiver_address="BENEFICIARY",
                refund_destination="SRC",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="integration-proof",
                currency="USD",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

    runtime.create_account("SRC", 200)
    runtime.create_account("pg-e2e-escrow", 0)
    runtime.create_account("BENEFICIARY", 0)

    funded = runtime.fund("pg-fund-1", "SRC", "T1", {"test": "fund"})
    assert funded["replayed"] is False

    locked = runtime.lock("pg-lock-1", "T2", {"test": "lock"})
    assert locked["replayed"] is False

    released = runtime.release(
        transaction_id="pg-release-1",
        destination="BENEFICIARY",
        timestamp="T3",
        evidence={"test": "release"},
        root=object(),
        owner_id="integration-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )
    assert released["replayed"] is False

    with session_factory() as session:
        escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == "pg-e2e-escrow")
        ).scalar_one()
        assert escrow.state == EscrowState.RELEASED.value

        balances = {
            row.account_id: row.balance
            for row in session.execute(select(LedgerAccountModel)).scalars()
        }
        assert balances["SRC"] == 100
        assert balances["pg-e2e-escrow"] == 0
        assert balances["BENEFICIARY"] == 100

        movements = session.execute(select(LedgerMovementModel)).scalars().all()
        assert len(movements) == 2
        assert {m.operation for m in movements} == {"FUND", "RELEASE"}

        witnesses = session.execute(select(TransactionWitness)).scalars().all()
        assert len(witnesses) == 3

        outbox = session.execute(select(OutboxEvent)).scalars().all()
        assert len(outbox) == 3

        idempotency = session.execute(select(DurableIdempotencyRecord)).scalars().all()
        assert len(idempotency) == 3
        assert all(row.state == "COMPLETED" for row in idempotency)

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()
