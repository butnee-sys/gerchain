from __future__ import annotations

from datetime import datetime, timezone

from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.canonical_ledger_read import CanonicalLedgerRead
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_factory_boots_and_uses_canonical_ledger(postgres_engine):
    config = ProductionRuntimeConfig(
        database_url=str(postgres_engine.url),
        escrow_id="prod-smoke-escrow",
        amount=100,
        currency="USD",
        witness_id="prod-smoke-witness",
    )
    factory = ProductionRuntimeFactory(config, engine=postgres_engine)
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    runtime.create_account("SMOKE-SOURCE", "USD", 1000)
    runtime.create_account("SMOKE-DEST", "USD", 0)

    with factory.session_factory() as session:
        session.add(
            CanonicalEscrow(
                id="prod-smoke-escrow",
                sender_address="SMOKE-SOURCE",
                receiver_address="SMOKE-DEST",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="production-smoke",
                refund_destination="SMOKE-SOURCE",
                currency="USD",
                version=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        session.commit()

    read = CanonicalLedgerRead(factory.session_factory())
    assert read.get_balance("SMOKE-SOURCE", "USD")["balance"] == 1000
    assert read.get_balance("SMOKE-DEST", "USD")["balance"] == 0
