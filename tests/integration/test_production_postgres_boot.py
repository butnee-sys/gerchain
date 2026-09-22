from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_factory_boots_and_canonical_ledger_moves_value():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, future=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-smoke-escrow",
            amount=100,
            currency="USD",
            witness_id="pg-smoke-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    with factory.session_factory() as session:
        runtime._canonical_ledger.create_account_in_transaction(
            session, "pg-source", "USD", 1000
        )
        runtime._canonical_ledger.create_account_in_transaction(
            session, "pg-destination", "USD", 0
        )
        runtime._canonical_ledger.transfer_in_transaction(
            session,
            "pg-smoke-transfer",
            "pg-source",
            "pg-destination",
            125,
            "USD",
        )
        session.commit()

        source = session.get(LedgerAccountModel, "pg-source")
        destination = session.get(LedgerAccountModel, "pg-destination")
        movement = session.execute(
            select(LedgerMovementModel).where(
                LedgerMovementModel.transaction_id == "pg-smoke-transfer"
            )
        ).scalar_one()

        assert source.balance == 875
        assert destination.balance == 125
        assert movement.amount == 125
        assert movement.currency == "USD"

    engine.dispose()
