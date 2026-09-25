from __future__ import annotations

from sqlalchemy import inspect

from services.gerchain_runtime_factory import ProductionRuntimeFactory


def test_production_factory_bootstraps_canonical_postgresql(
    canonical_postgresql_engine,
):
    runtime = ProductionRuntimeFactory.from_engine(
        escrow_id="production-smoke-escrow",
        amount=100,
        currency="MNT",
        witness_id="production-smoke-witness",
        engine=canonical_postgresql_engine,
    )

    assert runtime.is_canonical_ledger_authoritative

    tables = set(inspect(canonical_postgresql_engine).get_table_names())
    required = {
        "schema_version",
        "escrows",
        "gerchain_ledger_accounts",
        "gerchain_ledger_movements",
        "gerchain_transaction_witnesses",
        "gerchain_outbox_events",
        "gerchain_idempotency_records",
    }
    assert required <= tables
