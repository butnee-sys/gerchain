from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from persistence.atomic_ledger import LedgerAccountModel, PostgreSQLAtomicLedger
from persistence.cancel_escrow import cancel_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.settlement_coordinator import SettlementCoordinator
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


DATABASE_URL = os.environ.get("GERCHAIN_POSTGRES_DSN")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="GERCHAIN_POSTGRES_DSN is not configured",
)


def _escrow(session: Session, escrow_id: str, sender: str, receiver: str, amount: int) -> None:
    now = datetime.now(timezone.utc)
    session.add(
        CanonicalEscrow(
            id=escrow_id,
            sender_address=sender,
            receiver_address=receiver,
            amount=amount,
            state=EscrowState.CREATED.value,
            condition_desc="production re-performance",
            refund_destination=sender,
            currency="MNT",
            version=0,
            created_at=now,
            updated_at=now,
        )
    )


def _account(session: Session, account_id: str, balance: int) -> None:
    PostgreSQLAtomicLedger.create_account_in_transaction(
        session, account_id, "MNT", balance
    )


def test_eai_production_runtime_reperformance():
    escrow_id = f"eai-release-{uuid4().hex}"
    refund_id = f"eai-refund-{uuid4().hex}"
    cancel_id = f"eai-cancel-{uuid4().hex}"
    created_cancel_id = f"eai-created-cancel-{uuid4().hex}"
    settlement_id = f"eai-settlement-{uuid4().hex}"

    source = f"source-{uuid4().hex}"
    beneficiary = f"beneficiary-{uuid4().hex}"
    refund_source = f"refund-source-{uuid4().hex}"
    cancel_source = f"cancel-source-{uuid4().hex}"
    settlement_source = f"settlement-source-{uuid4().hex}"
    settlement_destination = f"settlement-destination-{uuid4().hex}"

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=DATABASE_URL,
            escrow_id=escrow_id,
            amount=40,
            currency="MNT",
            witness_id=f"witness-{uuid4().hex}",
        )
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    with factory.session_factory() as session:
        for account_id, balance in (
            (source, 100),
            (escrow_id, 0),
            (beneficiary, 0),
            (refund_source, 100),
            (refund_id, 0),
            (cancel_source, 100),
            (cancel_id, 0),
            (settlement_source, 50),
            (settlement_destination, 0),
        ):
            _account(session, account_id, balance)

        _escrow(session, escrow_id, source, beneficiary, 40)
        _escrow(session, refund_id, refund_source, f"unused-{refund_id}", 30)
        _escrow(session, cancel_id, cancel_source, f"unused-{cancel_id}", 20)
        _escrow(session, created_cancel_id, f"created-{created_cancel_id}", f"unused-{created_cancel_id}", 10)
        session.commit()

        fund_escrow_in_transaction(
            session,
            transaction_id=f"fund-{escrow_id}",
            escrow_id=escrow_id,
            source=source,
            amount=40,
            currency="MNT",
        )
        lock_escrow_in_transaction(
            session,
            transaction_id=f"lock-{escrow_id}",
            escrow_id=escrow_id,
        )
        release_escrow_in_transaction(
            session,
            transaction_id=f"release-{escrow_id}",
            escrow_id=escrow_id,
            beneficiary=beneficiary,
            amount=40,
            currency="MNT",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )

        fund_escrow_in_transaction(
            session,
            transaction_id=f"fund-{refund_id}",
            escrow_id=refund_id,
            source=refund_source,
            amount=30,
            currency="MNT",
        )
        lock_escrow_in_transaction(
            session,
            transaction_id=f"lock-{refund_id}",
            escrow_id=refund_id,
        )
        refund_escrow_in_transaction(
            session,
            transaction_id=f"refund-{refund_id}",
            escrow_id=refund_id,
            amount=30,
            currency="MNT",
        )

        fund_escrow_in_transaction(
            session,
            transaction_id=f"fund-{cancel_id}",
            escrow_id=cancel_id,
            source=cancel_source,
            amount=20,
            currency="MNT",
        )
        cancel_escrow_in_transaction(
            session,
            transaction_id=f"cancel-{cancel_id}",
            escrow_id=cancel_id,
        )

        cancel_escrow_in_transaction(
            session,
            transaction_id=f"cancel-{created_cancel_id}",
            escrow_id=created_cancel_id,
        )

        SettlementCoordinator(session).settle_in_transaction(
            transaction_id=f"settle-{settlement_id}",
            source=settlement_source,
            destination=settlement_destination,
            amount=15,
            currency="MNT",
        )
        session.commit()

        release_escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == escrow_id)
        ).scalar_one()
        refund_escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == refund_id)
        ).scalar_one()
        cancel_escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == cancel_id)
        ).scalar_one()
        created_cancel = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == created_cancel_id)
        ).scalar_one()

        assert release_escrow.state == EscrowState.RELEASED.value
        assert refund_escrow.state == EscrowState.REFUNDED.value
        assert cancel_escrow.state == EscrowState.CANCELLED.value
        assert created_cancel.state == EscrowState.CANCELLED.value

        balances = {
            row.account_id: row.balance
            for row in session.execute(select(LedgerAccountModel)).scalars()
            if row.account_id in {
                source, beneficiary, refund_source, refund_id,
                cancel_source, cancel_id, settlement_source,
                settlement_destination,
            }
        }
        assert balances[source] == 60
        assert balances[beneficiary] == 40
        assert balances[refund_source] == 100
        assert balances[refund_id] == 0
        assert balances[cancel_source] == 100
        assert balances[cancel_id] == 0
        assert balances[settlement_source] == 35
        assert balances[settlement_destination] == 15

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues
