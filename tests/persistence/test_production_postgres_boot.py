import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime_factory import ProductionRuntimeFactory


def test_production_runtime_boots_on_postgresql():
    database_url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(database_url, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    runtime = ProductionRuntimeFactory.create(
        escrow_id="postgres-smoke-escrow",
        amount=100,
        currency="USD",
        witness_id="postgres-smoke-witness",
        engine=engine,
        session_factory=session_factory,
    )
    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"
    with session_factory() as session:
        result = session.execute(text("select 1")).scalar_one()
        assert result == 1
    engine.dispose()
