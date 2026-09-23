import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime_factory import ProductionRuntimeFactory


def test_production_factory_rejects_non_postgresql_database():
    engine = create_engine("sqlite:///:memory:")
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with pytest.raises(ValueError, match="requires PostgreSQL"):
        ProductionRuntimeFactory.create(
            escrow_id="FACTORY-ESC",
            amount=100,
            currency="MNT",
            witness_id="FACTORY-W",
            engine=engine,
            session_factory=session_factory,
        )
    engine.dispose()
