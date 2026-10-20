import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from postgres.migrations import _canonical_migration_files
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_runtime_factory_establishes_canonical_authority():
    database_url = os.environ["GERCHAIN_TEST_DATABASE_URL"]
    engine = create_engine(database_url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="ea35-boot-escrow",
            amount=100,
            currency="USD",
            witness_id="ea35-boot-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    tables = set(inspect(engine).get_table_names())
    assert {
        "escrows",
        "gerchain_ledger_accounts",
        "gerchain_ledger_movements",
        "gerchain_transaction_witnesses",
        "gerchain_outbox_events",
        "gerchain_idempotency_records",
    }.issubset(tables)

    with engine.connect() as connection:
        versions = connection.execute(
            text("SELECT version FROM schema_version ORDER BY version")
        ).scalars().all()
        expected_versions = list(range(1, len(_canonical_migration_files(Path("postgres/migrations"))) + 1))
        assert versions == expected_versions

    engine.dispose()
