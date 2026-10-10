from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from postgres.migrations import apply_migrations
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory

DATABASE_URL = os.environ.get("GERCHAIN_POSTGRES_DSN")
MIGRATION_DIR = Path(__file__).resolve().parents[2] / "postgres" / "migrations"


def test_production_factory_and_canonical_runtime_postgresql():
    assert DATABASE_URL, "GERCHAIN_POSTGRES_DSN is required"

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            apply_migrations(conn, MIGRATION_DIR)

        factory = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=DATABASE_URL,
                escrow_id="eai-prod-1",
                amount=100,
                currency="MNT",
                witness_id="w-eai-prod-1",
            ),
            engine=engine,
        )
        runtime = factory.create()
        assert runtime.is_canonical_ledger_authoritative

        sf = factory.session_factory
        now = datetime.now(timezone.utc)
        with sf.begin() as session:
            session.add_all(
                [
                    LedgerAccountModel(
                        account_id="SRC",
                        currency="MNT",
                        balance=100,
                        version=0,
                        updated_at=now,
                    ),
                    LedgerAccountModel(
                        account_id="eai-prod-1",
                        currency="MNT",
                        balance=0,
                        version=0,
                        updated_at=now,
                    ),
                    LedgerAccountModel(
                        account_id="BEN",
                        currency="MNT",
                        balance=0,
                        version=0,
                        updated_at=now,
                    ),
                    CanonicalEscrow(
                        id="eai-prod-1",
                        sender_address="SRC",
                        receiver_address="BEN",
                        amount=100,
                        state=EscrowState.CREATED.value,
                        condition_desc="production-eai",
                        refund_destination="SRC",
                        currency="MNT",
                        version=0,
                        created_at=now,
                        updated_at=now,
                    ),
                ]
            )

        runtime.fund("fund-prod-1", "SRC", "T1", {"verified": True})
        runtime.lock("lock-prod-1", "T2", {"verified": True})
        runtime.release(
            transaction_id="release-prod-1",
            destination="BEN",
            timestamp="T3",
            evidence={"verified": True},
            root=object(),
            owner_id="production-test",
            authorized=True,
            evidence_verified=True,
            trinity_proof={"trust": True, "transparency": True, "performance": True},
        )

        with sf() as session:
            report = deep_reconcile_value_truth(session)
            assert report.matched, [issue.__dict__ for issue in report.issues]
            escrow = session.get(CanonicalEscrow, "eai-prod-1")
            assert escrow.state == EscrowState.RELEASED.value
            assert session.get(LedgerAccountModel, "SRC").balance == 0
            assert session.get(LedgerAccountModel, "BEN").balance == 100
            assert session.execute(text(
                "SELECT count(*) FROM gerchain_ledger_movements WHERE transaction_id IN ('fund-prod-1', 'release-prod-1')"
            )).scalar_one() == 2
    finally:
        engine.dispose()
