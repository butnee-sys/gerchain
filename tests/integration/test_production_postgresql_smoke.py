import os
import base64
from datetime import datetime, timezone

from sqlalchemy import select

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow
from dee_security.root_of_trust import RootOfTrust
from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)


def test_postgresql_production_value_flow():
    database_url = os.environ["GERCHAIN_DATABASE_URL"]

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="pg-smoke-escrow",
            amount=40,
            currency="USD",
            witness_id="pg-smoke-witness",
        )
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative

    with factory.session_factory() as session:
        session.query(LedgerAccountModel).filter(
            LedgerAccountModel.account_id.in_(
                ["pg-smoke-source", "pg-smoke-beneficiary", "pg-smoke-escrow"]
            )
        ).delete(synchronize_session=False)
        session.query(CanonicalEscrow).filter(
            CanonicalEscrow.id == "pg-smoke-escrow"
        ).delete(synchronize_session=False)

        now = datetime.now(timezone.utc)
        session.add_all(
            [
                LedgerAccountModel(
                    account_id="pg-smoke-source",
                    currency="USD",
                    balance=100,
                    version=0,
                    updated_at=now,
                ),
                LedgerAccountModel(
                    account_id="pg-smoke-beneficiary",
                    currency="USD",
                    balance=0,
                    version=0,
                    updated_at=now,
                ),
                LedgerAccountModel(
                    account_id="pg-smoke-escrow",
                    currency="USD",
                    balance=0,
                    version=0,
                    updated_at=now,
                ),
                CanonicalEscrow(
                    id="pg-smoke-escrow",
                    sender_address="pg-smoke-source",
                    receiver_address="pg-smoke-beneficiary",
                    amount=40,
                    state="CREATED",
                    condition_desc="production-smoke",
                    refund_destination="pg-smoke-source",
                    currency="USD",
                    version=0,
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        session.commit()

    runtime.fund(
        "pg-smoke-fund",
        "pg-smoke-source",
        "2026-09-30T00:00:00Z",
        {"test": "postgres-production"},
    )
    runtime.lock(
        "pg-smoke-lock",
        "2026-09-30T00:00:01Z",
        {"test": "postgres-production"},
    )
    runtime.release(
        root=RootOfTrust("pg-smoke-owner", base64.b64encode(bytes(32)).decode("ascii")),
        transaction_id="pg-smoke-release",
        destination="pg-smoke-beneficiary",
        timestamp="2026-09-30T00:00:02Z",
        evidence={"test": "postgres-production"},
        owner_id="pg-smoke-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={
            "trust": True,
            "transparency": True,
            "performance": True,
        },
    )

    with factory.session_factory() as session:
        source = session.execute(
            select(LedgerAccountModel).where(
                LedgerAccountModel.account_id == "pg-smoke-source"
            )
        ).scalar_one()
        beneficiary = session.execute(
            select(LedgerAccountModel).where(
                LedgerAccountModel.account_id == "pg-smoke-beneficiary"
            )
        ).scalar_one()
        escrow = session.execute(
            select(LedgerAccountModel).where(
                LedgerAccountModel.account_id == "pg-smoke-escrow"
            )
        ).scalar_one()
        canonical_escrow = session.execute(
            select(CanonicalEscrow).where(
                CanonicalEscrow.id == "pg-smoke-escrow"
            )
        ).scalar_one()

        report = deep_reconcile_value_truth(session)

        assert source.balance == 60
        assert beneficiary.balance == 40
        assert escrow.balance == 0
        assert canonical_escrow.state == "RELEASED"
        assert report.matched
        assert report.canonical_movement_count == 2
        assert report.witness_count == 3
        assert report.outbox_count == 3
        assert report.idempotency_count == 3
