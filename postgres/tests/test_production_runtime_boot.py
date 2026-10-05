from __future__ import annotations

import os

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_runtime_bootstraps_canonical_persistence():
    database_url = os.environ["GERCHAIN_POSTGRES_DSN"]
    engine = create_engine(database_url, future=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    runtime = ProductionRuntimeFactory(
        config=ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="smoke-escrow",
            amount=100,
            currency="MNT",
            witness_id="smoke-witness",
        ),
        engine=engine,
    ).create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    tables = set(inspect(engine).get_table_names())
    assert {
        "gerchain_ledger_accounts",
        "gerchain_ledger_movements",
        "escrows",
        "gerchain_outbox_events",
        "gerchain_idempotency_records",
        "gerchain_transaction_witnesses",
    } <= tables

    engine.dispose()
