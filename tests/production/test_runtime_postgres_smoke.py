from __future__ import annotations

import os

from sqlalchemy import inspect

from persistence.atomic_ledger import LedgerAccountModel
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_runtime_factory_boots_against_postgres():
    database_url = os.environ["GERCHAIN_DATABASE_URL"]
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="smoke-escrow",
            amount=100,
            currency="MNT",
            witness_id="smoke-witness",
        )
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert factory.engine.dialect.name == "postgresql"

    table_names = set(inspect(factory.engine).get_table_names())
    assert "gerchain_ledger_accounts" in table_names
    assert "gerchain_ledger_movements" in table_names
    assert "escrows" in table_names
    assert "gerchain_transaction_witnesses" in table_names
    assert "gerchain_outbox_events" in table_names
    assert "gerchain_idempotency_records" in table_names

    result = runtime.create_account("smoke-account", "MNT", 1000)
    assert result["balance"] == 1000
    assert runtime.get_balance("smoke-account")["balance"] == 1000

    factory.engine.dispose()
