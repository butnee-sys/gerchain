from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from persistence.atomic_ledger import LedgerAccountModel
from persistence.atomic_value_transaction import TransactionWitness
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.recovery_outbox import OutboxEvent
from persistence.durable_idempotency import DurableIdempotencyRecord
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


@pytest.fixture()
def production():
    url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_DATABASE_URL is required")
    config = ProductionRuntimeConfig(
        database_url=url,
        escrow_id="ea35-main-escrow",
        amount=100,
        currency="MNT",
        witness_id="ea35-main-witness",
    )
    factory = ProductionRuntimeFactory(config)
    runtime = factory.create()
    return factory, runtime


def test_postgresql_factory_and_fund_lock_release(production):
    factory, runtime = production
    assert runtime.is_canonical_ledger_authoritative

    sf = factory.session_factory
    now = datetime.now(timezone.utc)
    with sf.begin() as session:
        session.query(LedgerAccountModel).delete()
        session.query(CanonicalEscrow).delete()
        session.add_all([
            LedgerAccountModel(account_id="EA35-SOURCE", currency="MNT", balance=1000, version=0, updated_at=now),
            LedgerAccountModel(account_id="EA35-BEN", currency="MNT", balance=0, version=0, updated_at=now),
            LedgerAccountModel(account_id="ea35-main-escrow", currency="MNT", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="ea35-main-escrow",
                sender_address="EA35-SOURCE",
                receiver_address="EA35-BEN",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="EA35 PostgreSQL production proof",
                refund_destination="EA35-SOURCE",
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            ),
        ])

    with sf.begin() as session:
        funded = fund_escrow_in_transaction(
            session, transaction_id="EA35-FUND-1", escrow_id="ea35-main-escrow",
            source="EA35-SOURCE", amount=100, currency="MNT",
        )
        assert funded["replayed"] is False

    with sf.begin() as session:
        locked = lock_escrow_in_transaction(
            session, transaction_id="EA35-LOCK-1", escrow_id="ea35-main-escrow",
        )
        assert locked["replayed"] is False

    with sf.begin() as session:
        released = release_escrow_in_transaction(
            session,
            transaction_id="EA35-RELEASE-1",
            escrow_id="ea35-main-escrow",
            beneficiary="EA35-BEN",
            amount=100,
            currency="MNT",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        assert released["replayed"] is False

    with sf() as session:
        assert session.get(LedgerAccountModel, "EA35-SOURCE").balance == 900
        assert session.get(LedgerAccountModel, "EA35-BEN").balance == 100
        assert session.get(CanonicalEscrow, "ea35-main-escrow").state == EscrowState.RELEASED.value
        assert session.execute(select(TransactionWitness)).scalars().all()
        assert session.execute(select(OutboxEvent)).scalars().all()
        assert session.execute(select(DurableIdempotencyRecord)).scalars().all()
