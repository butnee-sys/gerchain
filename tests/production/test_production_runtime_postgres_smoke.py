from __future__ import annotations

from datetime import datetime, timezone

from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.canonical_ledger_read import CanonicalLedgerRead

from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.cancel_escrow import cancel_escrow_in_transaction
from persistence.settlement_coordinator import SettlementCoordinator
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
    runtime.create_account("prod-smoke-escrow", 0)

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


def test_production_factory_executes_refund_cancel_and_settlement_on_real_postgresql(postgres_engine):
    config = ProductionRuntimeConfig(
        database_url=str(postgres_engine.url), escrow_id="prod-eai-escrow", amount=100,
        currency="USD", witness_id="prod-eai-witness",
    )
    factory = ProductionRuntimeFactory(config, engine=postgres_engine)
    runtime = factory.create()

    for account, balance in (("EAI-SOURCE", 1000), ("EAI-DEST", 0),
                             ("prod-eai-escrow", 0), ("EAI-CANCEL-ESC", 0),
                             ("EAI-SETTLE-DEST", 0)):
        runtime.create_account(account, balance)

    now = datetime.now(timezone.utc)
    with factory.session_factory() as session:
        session.add_all([
            CanonicalEscrow(id="prod-eai-escrow", sender_address="EAI-SOURCE",
                receiver_address="EAI-DEST", amount=100, state=EscrowState.CREATED.value,
                condition_desc="refund-smoke", refund_destination="EAI-SOURCE", currency="USD",
                version=0, created_at=now, updated_at=now),
            CanonicalEscrow(id="EAI-CANCEL-ESC", sender_address="EAI-SOURCE",
                receiver_address="EAI-DEST", amount=50, state=EscrowState.CREATED.value,
                condition_desc="cancel-smoke", refund_destination="EAI-SOURCE", currency="USD",
                version=0, created_at=now, updated_at=now),
        ])
        session.commit()

    with factory.session_factory() as session:
        fund_escrow_in_transaction(session, transaction_id="eai-refund-fund",
            escrow_id="prod-eai-escrow", source="EAI-SOURCE", amount=100, currency="USD")
        lock_escrow_in_transaction(session, transaction_id="eai-refund-lock", escrow_id="prod-eai-escrow")
        session.commit()

    with factory.session_factory() as session:
        refunded = refund_escrow_in_transaction(session, transaction_id="eai-refund-1",
            escrow_id="prod-eai-escrow", amount=100, currency="USD", payload={"evidence":"production"})
        session.commit()
        assert refunded["replayed"] is False

    with factory.session_factory() as session:
        fund_escrow_in_transaction(session, transaction_id="eai-cancel-fund",
            escrow_id="EAI-CANCEL-ESC", source="EAI-SOURCE", amount=50, currency="USD")
        cancelled = cancel_escrow_in_transaction(session, transaction_id="eai-cancel-1", escrow_id="EAI-CANCEL-ESC")
        session.commit()
        assert cancelled["replayed"] is False

    with factory.session_factory() as session:
        settled = SettlementCoordinator(session).settle_in_transaction(
            transaction_id="eai-settlement-1", source="EAI-SOURCE", destination="EAI-SETTLE-DEST",
            amount=25, currency="USD")
        session.commit()
        assert settled["replayed"] is False

    with factory.session_factory() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched

    read = CanonicalLedgerRead(factory.session_factory())
    assert read.get_balance("EAI-SOURCE", "USD") == 975
    assert read.get_balance("EAI-DEST", "USD") == 0
    assert read.get_balance("EAI-SETTLE-DEST", "USD") == 25