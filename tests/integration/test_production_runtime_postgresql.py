from __future__ import annotations

import os

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_runtime_boots_against_real_postgresql() -> None:
    database_url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(database_url, pool_pre_ping=True)
    runtime = ProductionRuntimeFactory.create(
        escrow_id="pg-boot-escrow",
        amount=100,
        currency="USD",
        witness_id="pg-boot-witness",
        engine=engine,
        session_factory=sessionmaker(bind=engine, expire_on_commit=False),
    )


    assert runtime.is_canonical_ledger_authoritative

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

    engine.dispose()
