import os

from sqlalchemy import text

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_runtime_boots_on_postgresql():
    database_url = os.environ["GERCHAIN_DATABASE_URL"]
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="postgres-smoke-escrow",
            amount=100,
            currency="USD",
            witness_id="postgres-smoke-witness",
        )
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"
    with factory.session_factory() as session:
        result = session.execute(text("select 1")).scalar_one()
        assert result == 1
    factory.engine.dispose()
