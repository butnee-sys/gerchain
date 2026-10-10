from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.cancel_escrow import cancel_escrow_in_transaction
from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
    initialize_canonical_postgres_schema,
)


POSTGRES_URL = os.getenv("TEST_POSTGRES_URL")


@pytest.mark.skipif(not POSTGRES_URL, reason="TEST_POSTGRES_URL is required")
def test_production_postgres_full_value_flow():
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    # ProductionRuntimeFactory.create() intentionally fails closed unless the
    # configured escrow already exists in canonical PostgreSQL truth. Prepare
    # the schema and seed the three test aggregates before booting the runtime.
    initialize_canonical_postgres_schema(engine)
    now = datetime.now(timezone.utc)
    with sessionmaker(bind=engine, expire_on_commit=False)() as seed_session:
        for escrow_id, sender, receiver, refund in (
            ("esc-release", "SRC", "BEN", "REF"),
            ("esc-refund", "SRC", "BEN", "REF"),
            ("esc-cancel", "SRC", "BEN", "REF"),
        ):
            seed_session.add(
                CanonicalEscrow(
                    id=escrow_id,
                    sender_address=sender,
                    receiver_address=receiver,
                    amount=100,
                    state=EscrowState.CREATED.value,
                    condition_desc="production integration test",
                    refund_destination=refund,
                    currency="MNT",
                    version=0,
                    created_at=now,
                    updated_at=now,
                )
            )
        seed_session.commit()

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=POSTGRES_URL,
            escrow_id="esc-release",
            amount=100,
            currency="MNT",
            witness_id="w-production",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        for account, balance in (
            ("SRC", 300),
            ("esc-release", 0),
            ("esc-refund", 0),
            ("esc-cancel", 0),
            ("BEN", 0),
            ("REF", 0),
        ):
            session.add(
                LedgerAccountModel(
                    account_id=account,
                    currency="MNT",
                    balance=balance,
                    version=0,
                    updated_at=now,
                )
            )

        session.commit()

        # FUND + LOCK + RELEASE
        fund_escrow_in_transaction(
            session,
            transaction_id="pg-fund-release",
            escrow_id="esc-release",
            source="SRC",
            amount=100,
            currency="MNT",
        )
        lock_escrow_in_transaction(
            session,
            transaction_id="pg-lock-release",
            escrow_id="esc-release",
        )
        release_escrow_in_transaction(
            session,
            transaction_id="pg-release",
            escrow_id="esc-release",
            beneficiary="BEN",
            amount=100,
            currency="MNT",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )

        # FUND + LOCK + REFUND
        fund_escrow_in_transaction(
            session,
            transaction_id="pg-fund-refund",
            escrow_id="esc-refund",
            source="SRC",
            amount=100,
            currency="MNT",
        )
        lock_escrow_in_transaction(
            session,
            transaction_id="pg-lock-refund",
            escrow_id="esc-refund",
        )
        refund_escrow_in_transaction(
            session,
            transaction_id="pg-refund",
            escrow_id="esc-refund",
            amount=100,
            currency="MNT",
        )

        # FUND + CANCEL: cancellation reverses to authoritative sender.
        fund_escrow_in_transaction(
            session,
            transaction_id="pg-fund-cancel",
            escrow_id="esc-cancel",
            source="SRC",
            amount=100,
            currency="MNT",
        )
        cancel_escrow_in_transaction(
            session,
            transaction_id="pg-cancel",
            escrow_id="esc-cancel",
        )
        session.commit()

        states = dict(
            session.execute(
                select(CanonicalEscrow.id, CanonicalEscrow.state)
                .where(CanonicalEscrow.id.in_(
                    ["esc-release", "esc-refund", "esc-cancel"]
                ))
            ).all()
        )
        assert states == {
            "esc-release": "RELEASED",
            "esc-refund": "REFUNDED",
            "esc-cancel": "CANCELLED",
        }

        balances = dict(
            session.execute(
                select(LedgerAccountModel.account_id, LedgerAccountModel.balance)
            ).all()
        )
        assert balances["SRC"] == 100
        assert balances["BEN"] == 100
        assert balances["REF"] == 100

        report = deep_reconcile_value_truth(session)
        assert report.matched, [f"{i.code}: {i.detail}" for i in report.issues]

    engine.dispose()
