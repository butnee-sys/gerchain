import os

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


@pytest.mark.integration
def test_production_runtime_boots_against_postgresql():
    database_url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = None
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="integration-escrow",
            amount=100,
            currency="USD",
            witness_id="integration-witness",
        )
    )
    engine = factory.engine
    try:
        runtime = factory.create()
        assert runtime.is_canonical_ledger_authoritative

        Session = sessionmaker(bind=engine, expire_on_commit=False)
        with Session() as session:
            session.add(
                LedgerAccountModel(
                    account_id="integration-account",
                    currency="USD",
                    balance=100,
                    version=0,
                    updated_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
                )
            )
            session.commit()
            row = session.execute(
                select(LedgerAccountModel).where(
                    LedgerAccountModel.account_id == "integration-account"
                )
            ).scalar_one()
            assert row.balance == 100
    finally:
        engine.dispose()
