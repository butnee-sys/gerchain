from __future__ import annotations

import os

from sqlalchemy import create_engine, inspect

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_postgresql_boot_establishes_canonical_authority() -> None:
    database_url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(database_url, future=True)
    try:
        runtime = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=os.environ["GERCHAIN_DATABASE_URL"],
                escrow_id="ci-escrow",
                amount=100,
                currency="MNT",
                witness_id="ci-witness",
            ),
            engine=engine,
        ).create()

        assert runtime.is_canonical_ledger_authoritative is True

        inspector = inspect(engine)
        required = {
            "escrows",
            "gerchain_ledger_accounts",
            "gerchain_ledger_movements",
            "gerchain_transaction_witnesses",
            "gerchain_outbox_events",
            "gerchain_idempotency_records",
        }
        assert required.issubset(set(inspector.get_table_names()))
    finally:
        engine.dispose()
