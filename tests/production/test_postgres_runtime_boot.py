import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory
from persistence.atomic_ledger import LedgerAccountModel


def test_production_factory_boots_against_postgresql():
    database_url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(database_url, pool_pre_ping=True)

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="ci-escrow",
            amount=100,
            currency="MNT",
            witness_id="ci-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()

    assert engine.dialect.name == "postgresql"
    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    with Session(engine) as session:
        assert session.execute(select(LedgerAccountModel)).all() == []

    engine.dispose()
