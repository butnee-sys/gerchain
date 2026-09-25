from __future__ import annotations

from datetime import datetime, timezone

from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.canonical_ledger_read import CanonicalLedgerRead

from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
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

    runtime.create_account("SMOKE-SOURCE", 1000)
    runtime.create_account("SMOKE-DEST", 0)

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
    assert read.get_balance("SMOKE-SOURCE", "USD") == 1000
    assert read.get_balance("SMOKE-DEST", "USD") == 0


    with factory.session_factory() as session:
        funded = fund_escrow_in_transaction(
            session,
            transaction_id="smoke-fund-1",
            escrow_id="prod-smoke-escrow",
            source="SMOKE-SOURCE",
            amount=100,
            currency="USD",
        )
        session.commit()
        assert funded["replayed"] is False

    with factory.session_factory() as session:
        locked = lock_escrow_in_transaction(
            session,
            transaction_id="smoke-lock-1",
            escrow_id="prod-smoke-escrow",
        )
        session.commit()
        assert locked["replayed"] is False

    release_payload = {
        "timestamp": "SMOKE",
        "evidence": "integration",
        "owner_id": "smoke-owner",
    }
    with factory.session_factory() as session:
        released = release_escrow_in_transaction(
            session,
            transaction_id="smoke-release-1",
            escrow_id="prod-smoke-escrow",
            beneficiary="SMOKE-DEST",
            amount=100,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
            payload=release_payload,
        )
        session.commit()
        assert released["replayed"] is False

    with factory.session_factory() as session:
        replay = release_escrow_in_transaction(
            session,
            transaction_id="smoke-release-1",
            escrow_id="prod-smoke-escrow",
            beneficiary="SMOKE-DEST",
            amount=100,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
            payload=release_payload,
        )
        session.commit()
        assert replay["replayed"] is True

    with factory.session_factory() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, [f"{i.code}: {i.detail}" for i in report.issues]

    read = CanonicalLedgerRead(factory.session_factory())
    assert read.get_balance("SMOKE-SOURCE", "USD") == 900
    assert read.get_balance("SMOKE-DEST", "USD") == 100
