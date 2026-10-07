from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from persistence.atomic_ledger import LedgerAccountModel
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.canonical_ledger_read import CanonicalLedgerRead
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_postgresql_factory_and_canonical_read():
    database_url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(database_url, pool_pre_ping=True)
    config = ProductionRuntimeConfig(
        database_url=database_url,
        escrow_id="pg-smoke-escrow",
        amount=100,
        currency="USD",
        witness_id="pg-smoke-witness",
    )
    runtime = ProductionRuntimeFactory(config, engine=engine).create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        session.add_all([
            LedgerAccountModel(account_id="pg-smoke-source", currency="USD", balance=1000, version=0, updated_at=now),
            LedgerAccountModel(account_id="pg-smoke-escrow", currency="USD", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="pg-smoke-escrow",
                sender_address="pg-smoke-source",
                receiver_address="pg-smoke-beneficiary",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="production smoke test",
                refund_destination="pg-smoke-source",
                currency="USD",
                version=0,
                created_at=now,
                updated_at=now,
            ),
        ])
        session.commit()

    with Session(engine) as session:
        read = CanonicalLedgerRead(lambda: session)
        assert read.get_balance("pg-smoke-source", "USD")["balance"] == 1000
        assert read.get_balance("pg-smoke-escrow", "USD")["balance"] == 0
        escrow = session.get(CanonicalEscrow, "pg-smoke-escrow")
        assert escrow is not None
        assert escrow.state == EscrowState.CREATED.value

    engine.dispose()
