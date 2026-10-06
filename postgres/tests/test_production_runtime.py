from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.cancel_escrow import cancel_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.settlement_coordinator import SettlementCoordinator
from services.gerchain_runtime_factory import ProductionRuntimeFactory


DATABASE_URL = os.environ.get("GERCHAIN_POSTGRES_DSN")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="GERCHAIN_POSTGRES_DSN is not configured",
)


def _session_factory():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return engine, factory


def _seed_account(session, account_id: str, balance: int) -> None:
    session.add(
        LedgerAccountModel(
            account_id=account_id,
            currency="USD",
            balance=balance,
            version=0,
            updated_at=datetime.now(timezone.utc),
        )
    )


def _seed_escrow(session, escrow_id: str, sender: str, receiver: str, refund: str) -> None:
    now = datetime.now(timezone.utc)
    session.add(
        CanonicalEscrow(
            id=escrow_id,
            sender_address=sender,
            receiver_address=receiver,
            amount=100,
            state=EscrowState.CREATED.value,
            condition_desc="production-gate",
            refund_destination=refund,
            currency="USD",
            version=0,
            created_at=now,
            updated_at=now,
        )
    )


def test_production_runtime_boot_and_canonical_value_flow():
    engine, factory = _session_factory()
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "TRUNCATE gerchain_transaction_witnesses, "
                    "gerchain_outbox_events, gerchain_idempotency_records, "
                    "gerchain_ledger_movements, gerchain_ledger_accounts, escrows CASCADE"
                )
            )

        runtime = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=DATABASE_URL,
                escrow_id="gate-release",
                amount=100,
                currency="USD",
                witness_id="gate-witness",
            ),
            engine=engine,
        ).create()
        assert runtime.is_canonical_ledger_authoritative

        with factory() as session:
            _seed_account(session, "sender-release", 100)
            _seed_account(session, "receiver-release", 0)
            _seed_account(session, "sender-refund", 100)
            _seed_account(session, "receiver-refund", 0)
            _seed_account(session, "sender-cancel", 100)
            _seed_account(session, "receiver-cancel", 0)
            _seed_account(session, "settle-source", 100)
            _seed_account(session, "settle-dest", 0)
            _seed_escrow(session, "gate-release", "sender-release", "receiver-release", "sender-release")
            _seed_escrow(session, "gate-refund", "sender-refund", "receiver-refund", "sender-refund")
            _seed_escrow(session, "gate-cancel", "sender-cancel", "receiver-cancel", "sender-cancel")
            session.commit()

        with factory() as session:
            fund_escrow_in_transaction(
                session,
                transaction_id="gate-fund-release",
                escrow_id="gate-release",
                source="sender-release",
                amount=100,
                currency="USD",
            )
            session.commit()

        with factory() as session:
            lock_escrow_in_transaction(
                session,
                transaction_id="gate-lock-release",
                escrow_id="gate-release",
            )
            session.commit()

        with factory() as session:
            release_escrow_in_transaction(
                session,
                transaction_id="gate-release-tx",
                escrow_id="gate-release",
                beneficiary="receiver-release",
                amount=100,
                currency="USD",
                decision_status="APPROVE",
                authorization_status="AUTHORIZED",
                trust=True,
                transparency=True,
                performance=True,
                evidence_verified=True,
            )
            session.commit()

        with factory() as session:
            fund_escrow_in_transaction(
                session,
                transaction_id="gate-fund-refund",
                escrow_id="gate-refund",
                source="sender-refund",
                amount=100,
                currency="USD",
            )
            lock_escrow_in_transaction(
                session,
                transaction_id="gate-lock-refund",
                escrow_id="gate-refund",
            )
            session.commit()

        with factory() as session:
            refund_escrow_in_transaction(
                session,
                transaction_id="gate-refund-tx",
                escrow_id="gate-refund",
                amount=100,
                currency="USD",
            )
            session.commit()

        with factory() as session:
            fund_escrow_in_transaction(
                session,
                transaction_id="gate-fund-cancel",
                escrow_id="gate-cancel",
                source="sender-cancel",
                amount=100,
                currency="USD",
            )
            session.commit()

        with factory() as session:
            cancel_escrow_in_transaction(
                session,
                transaction_id="gate-cancel-tx",
                escrow_id="gate-cancel",
            )
            session.commit()

        with factory() as session:
            SettlementCoordinator(session).settle_in_transaction(
                transaction_id="gate-settlement-tx",
                source="settle-source",
                destination="settle-dest",
                amount=25,
                currency="USD",
            )
            session.commit()

        with factory() as session:
            report = deep_reconcile_value_truth(session)
            assert report.matched, [(i.code, i.transaction_id, i.detail) for i in report.issues]

            states = dict(
                session.execute(
                    select(CanonicalEscrow.id, CanonicalEscrow.state)
                    .where(CanonicalEscrow.id.in_(
                        ["gate-release", "gate-refund", "gate-cancel"]
                    ))
                ).all()
            )
            assert states == {
                "gate-release": "RELEASED",
                "gate-refund": "REFUNDED",
                "gate-cancel": "CANCELLED",
            }
    finally:
        engine.dispose()
