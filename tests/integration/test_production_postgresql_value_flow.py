from datetime import datetime, timezone
import os

from sqlalchemy import select

from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.atomic_ledger import LedgerMovementModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_postgresql_fund_lock_release_and_deep_truth():
    database_url = os.environ["GERCHAIN_DATABASE_URL"]
    escrow_id = "pg-smoke-escrow"
    amount = 40
    currency = "USD"

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id=escrow_id,
            amount=amount,
            currency=currency,
            witness_id="pg-smoke-witness",
        )
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    runtime.create_account("PG-SOURCE", initial_balance=100)
    runtime.create_account("PG-DEST", initial_balance=0)
    runtime.create_account(escrow_id, initial_balance=0)

    now = datetime.now(timezone.utc)
    with factory.session_factory() as session:
        session.add(
            CanonicalEscrow(
                id=escrow_id,
                sender_address="PG-SOURCE",
                receiver_address="PG-DEST",
                refund_destination="PG-SOURCE",
                amount=amount,
                state=EscrowState.CREATED.value,
                condition_desc="production-postgresql-smoke",
                currency=currency,
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

    runtime.fund("pg-fund-1", "PG-SOURCE", now.isoformat(), {"source": "ci"})
    assert runtime.get_balance("PG-SOURCE") == 60
    assert runtime.get_balance(escrow_id) == 40

    runtime.lock("pg-lock-1", now.isoformat(), {"source": "ci"})
    assert runtime.get_escrow_state()["state"] == EscrowState.LOCKED.value

    runtime.release(
        transaction_id="pg-release-1",
        destination="PG-DEST",
        timestamp=now.isoformat(),
        evidence={"source": "ci"},
        root=object(),
        owner_id="ci-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={
            "trust": True,
            "transparency": True,
            "performance": True,
        },
    )

    assert runtime.get_balance(escrow_id) == 0
    assert runtime.get_balance("PG-DEST") == 40
    assert runtime.get_escrow_state()["state"] == EscrowState.RELEASED.value

    with factory.session_factory() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, [f"{i.code}:{i.transaction_id}:{i.detail}" for i in report.issues]
        movement_count = len(session.execute(select(LedgerMovementModel)).scalars().all())
        assert movement_count == 2

    factory.engine.dispose()
