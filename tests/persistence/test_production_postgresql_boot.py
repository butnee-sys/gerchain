from __future__ import annotations

import os

from sqlalchemy import create_engine, text

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_postgresql_boot_and_schema_guard():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    try:
        runtime = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=url,
                escrow_id="boot-escrow",
                amount=100,
                currency="MNT",
                witness_id="boot-witness",
            ),
            engine=engine,
        ).create()

        assert runtime.is_canonical_ledger_authoritative

        with engine.connect() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    text(
                        """
                        SELECT tablename
                        FROM pg_tables
                        WHERE schemaname = 'public'
                        """
                    )
                )
            }

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
    finally:
        engine.dispose()
