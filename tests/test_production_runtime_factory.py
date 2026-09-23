import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_factory_rejects_non_postgresql_database():
    engine = create_engine("sqlite:///:memory:")
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with pytest.raises(ValueError, match="requires PostgreSQL"):
        ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url="sqlite:///:memory:",
                escrow_id="FACTORY-ESC",
                amount=100,
                currency="MNT",
                witness_id="FACTORY-W",
            ),
            engine=engine,
        )
    engine.dispose()
