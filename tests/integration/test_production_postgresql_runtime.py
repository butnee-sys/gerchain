from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
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
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


DATABASE_URL = os.environ.get("GERCHAIN_DATABASE_URL")
pytestmark = __import__("pytest").mark.skipif(
    not DATABASE_URL,
    reason="GERCHAIN_DATABASE_URL is required for PostgreSQL production re-performance",
)


def _factory():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=DATABASE_URL,
            escrow_id="ci-bootstrap",
            amount=1,
            currency="USD",
            witness_id="ci-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def _account(session, account_id: str, balance: int) -> None:
    existing = session.execute(
        select(LedgerAccountModel).where(LedgerAccountModel.account_id == account_id)
    ).scalar_one_or_none()
    if existing is None:
        session.add(
            LedgerAccountModel(
                account_id=account_id,
                currency="USD",
                balance=balance,
                version=0,
                updated_at=datetime.now(timezone.utc),
            )
        )


def _escrow(session, escrow_id: str, sender: str, receiver: str, refund: str) -> None:
    session.merge(
        CanonicalEscrow(
            id=escrow_id,
            sender_address=sender,
            receiver_address=receiver,
            refund_destination=refund,
            amount=10,
            currency="USD",
            state=EscrowState.CREATED.value,
            condition_desc="CI production re-performance",
            version=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )


def test_production_postgresql_full_value_flow_and_reconciliation():
    engine, sessions = _factory()
    try:
        with sessions() as session:
            for account, balance in (
                ("ci-source-release", 100),
                ("ci-beneficiary", 0),
                ("ci-source-refund", 100),
                ("ci-refund-destination", 0),
                ("ci-source-cancel", 100),
                ("ci-source-settlement", 50),
                ("ci-settlement-destination", 0),
            ):
                _account(session, account, balance)

            _escrow(session, "ci-release", "ci-source-release", "ci-beneficiary", "ci-source-release")
            _escrow(session, "ci-refund", "ci-source-refund", "ci-beneficiary", "ci-refund-destination")
            _escrow(session, "ci-cancel", "ci-source-cancel", "ci-beneficiary", "ci-source-cancel")
            session.commit()

        with sessions() as session:
            fund_escrow_in_transaction(
                session,
                transaction_id="ci-fund-release",
                escrow_id="ci-release",
                source="ci-source-release",
                amount=10,
                currency="USD",
            )
            session.commit()

        with sessions() as session:
            lock_escrow_in_transaction(
                session,
                transaction_id="ci-lock-release",
                escrow_id="ci-release",
            )
            session.commit()

        with sessions() as session:
            release_escrow_in_transaction(
                session,
                transaction_id="ci-release",
                escrow_id="ci-release",
                beneficiary="ci-beneficiary",
                amount=10,
                currency="USD",
                decision_status="APPROVE",
                authorization_status="AUTHORIZED",
                trust=True,
                transparency=True,
                performance=True,
                evidence_verified=True,
            )
            session.commit()

        with sessions() as session:
            fund_escrow_in_transaction(
                session,
                transaction_id="ci-fund-refund",
                escrow_id="ci-refund",
                source="ci-source-refund",
                amount=10,
                currency="USD",
            )
            session.commit()

        with sessions() as session:
            lock_escrow_in_transaction(
                session,
                transaction_id="ci-lock-refund",
                escrow_id="ci-refund",
            )
            session.commit()

        with sessions() as session:
            refund_escrow_in_transaction(
                session,
                transaction_id="ci-refund",
                escrow_id="ci-refund",
                amount=10,
                currency="USD",
            )
            session.commit()

        with sessions() as session:
            cancel_escrow_in_transaction(
                session,
                transaction_id="ci-cancel",
                escrow_id="ci-cancel",
            )
            session.commit()

        with sessions() as session:
            SettlementCoordinator(session).settle_in_transaction(
                transaction_id="ci-settlement",
                source="ci-source-settlement",
                destination="ci-settlement-destination",
                amount=10,
                currency="USD",
            )
            session.commit()

        with sessions() as session:
            report = deep_reconcile_value_truth(session)
            assert report.matched, [issue.__dict__ for issue in report.issues]
            assert session.execute(
                select(CanonicalEscrow.state).where(CanonicalEscrow.id == "ci-release")
            ).scalar_one() == EscrowState.RELEASED.value
            assert session.execute(
                select(CanonicalEscrow.state).where(CanonicalEscrow.id == "ci-refund")
            ).scalar_one() == EscrowState.REFUNDED.value
            assert session.execute(
                select(CanonicalEscrow.state).where(CanonicalEscrow.id == "ci-cancel")
            ).scalar_one() == EscrowState.CANCELLED.value
    finally:
        engine.dispose()
