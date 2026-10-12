from __future__ import annotations

import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime_factory import ProductionRuntimeFactory


def test_production_runtime_bootstraps_canonical_persistence():
    database_url = os.environ["GERCHAIN_POSTGRES_DSN"]
    engine = create_engine(database_url, future=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    runtime = ProductionRuntimeFactory.create(
        escrow_id="smoke-escrow",
        amount=100,
        currency="MNT",
        witness_id="smoke-witness",
        engine=engine,
        session_factory=session_factory,
    )

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    # Second invocation proves the production migration path is repeat-safe.
    second_runtime = ProductionRuntimeFactory.create(
        escrow_id="smoke-escrow",
        amount=100,
        currency="MNT",
        witness_id="smoke-witness",
        engine=engine,
        session_factory=session_factory,
    )
    assert second_runtime.is_canonical_ledger_authoritative

    with engine.connect() as connection:
        versions = connection.execute(
            text("SELECT version FROM schema_version ORDER BY version")
        ).scalars().all()
        assert versions == list(range(1, 7)), versions
        rows = connection.execute(text(
            "SELECT c.relname, pg_get_constraintdef(k.oid) "
            "FROM pg_constraint k JOIN pg_class c ON c.oid = k.conrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'public' AND c.relname IN "
            "('escrows', 'gerchain_ledger_movements', "
            "'gerchain_transaction_witnesses', 'gerchain_idempotency_records') "
            "ORDER BY c.relname, k.conname"
        )).all()
        definitions = [(row[0], row[1]) for row in rows]
        print("CANONICAL_POSTGRES_CONSTRAINTS", definitions)
        assert any(table == "escrows" and "state" in definition.lower()
                   and "CANCELLED" in definition for table, definition in definitions)
        assert any(table == "gerchain_ledger_movements"
                   and "amount" in definition.lower() and "> 0" in definition
                   for table, definition in definitions)
        assert any(table == "gerchain_ledger_movements"
                   and "transaction_id" in definition.lower()
                   and "UNIQUE" in definition.upper()
                   for table, definition in definitions)

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
