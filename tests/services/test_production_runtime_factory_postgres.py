import os

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_runtime_factory_establishes_canonical_authority():
    database_url = os.environ["GERCHAIN_TEST_DATABASE_URL"]
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="ea35-boot-escrow",
            amount=100,
            currency="USD",
            witness_id="ea35-boot-witness",
        )
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"
    factory.engine.dispose()
