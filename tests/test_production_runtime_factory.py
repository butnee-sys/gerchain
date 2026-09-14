from services.production_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_factory_builds_postgresql_authoritative_runtime(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'runtime.db'}"
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="FACTORY-ESC",
            amount=100,
            currency="MNT",
            witness_id="FACTORY-W",
        )
    )
    runtime = factory.create()
    assert runtime.is_postgresql_authoritative is True
    assert runtime.runtime_mode == "production-postgresql"
    runtime.require_postgresql_authority()
