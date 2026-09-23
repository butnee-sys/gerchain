import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


pytestmark = pytest.mark.integration


def test_production_postgresql_boot_and_canonical_value_flow():
    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_DATABASE_URL is required for PostgreSQL integration")

    escrow_id = "integration-escrow"
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id=escrow_id,
            amount=100,
            currency="MNT",
            witness_id="integration-witness",
        )
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    now = datetime.now(timezone.utc)
    with factory.session_factory() as session:
        session.add_all([
            LedgerAccountModel(account_id="integration-source", currency="MNT", balance=100, version=0, updated_at=now),
            LedgerAccountModel(account_id="integration-beneficiary", currency="MNT", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id=escrow_id,
                sender_address="integration-source",
                receiver_address="integration-beneficiary",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="integration",
                refund_destination="integration-source",
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            ),
        ])
        session.commit()

    runtime.fund("integration-fund", "integration-source", "T0", {"integration": True})
    runtime.lock("integration-lock", "T1", {"integration": True})
    runtime.release(
        transaction_id="integration-release",
        destination="integration-beneficiary",
        timestamp="T2",
        evidence={"integration": True},
        owner_id="integration-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={
            "trust": True,
            "transparency": True,
            "performance": True,
        },
        root=object(),
    )

    with factory.session_factory() as session:
        escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == escrow_id)
        ).scalar_one()
        source = session.execute(
            select(LedgerAccountModel).where(LedgerAccountModel.account_id == "integration-source")
        ).scalar_one()
        beneficiary = session.execute(
            select(LedgerAccountModel).where(LedgerAccountModel.account_id == "integration-beneficiary")
        ).scalar_one()
        report = deep_reconcile_value_truth(session)

        assert escrow.state == EscrowState.RELEASED.value
        assert source.balance == 0
        assert beneficiary.balance == 100
        assert report.matched
        assert report.canonical_movement_count == 2

    factory.engine.dispose()
