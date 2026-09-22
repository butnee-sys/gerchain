import pytest

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_factory_rejects_non_postgresql_database(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'runtime.db'}"
    with pytest.raises(ValueError, match="requires PostgreSQL"):
        ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=database_url,
                escrow_id="FACTORY-ESC",
                amount=100,
                currency="MNT",
                witness_id="FACTORY-W",
            )
        )
