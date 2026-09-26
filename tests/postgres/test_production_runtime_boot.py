from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text

from services.gerchain_runtime_factory import ProductionRuntimeFactory


DATABASE_URL = os.environ.get("GERCHAIN_POSTGRES_DSN")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="GERCHAIN_POSTGRES_DSN is not configured",
)


def test_production_runtime_boot_establishes_canonical_ledger_authority() -> None:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        runtime = ProductionRuntimeFactory.from_engine(
            escrow_id="production-boot-escrow",
            amount=100,
            currency="MNT",
            witness_id="production-boot-witness",
            engine=engine,
        )

        assert runtime.is_canonical_ledger_authoritative
        assert runtime.runtime_mode == "production-postgresql"

        runtime.create_account("production-boot-source", initial_balance=1000)
        assert runtime.get_balance("production-boot-source") == 1000

        with engine.connect() as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    text(
                        """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        """
                    )
                )
            }

        required = {
            "escrows",
            "gerchain_ledger_accounts",
            "gerchain_ledger_movements",
            "gerchain_transaction_witnesses",
            "gerchain_outbox_events",
            "gerchain_idempotency_records",
            "schema_version",
        }
        assert required <= tables
    finally:
        engine.dispose()
