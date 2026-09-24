from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from persistence.atomic_ledger import LedgerAccountModel
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.cancel_escrow import cancel_escrow_in_transaction
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


@pytest.fixture()
def factory():
    url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_DATABASE_URL is required")
    return ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="ea35-refund-escrow",
            amount=100,
            currency="MNT",
            witness_id="ea35-refund-witness",
        )
    )


def test_postgresql_refund_uses_authoritative_destination(factory):
    factory.create()
    sf = factory.session_factory
    now = datetime.now(timezone.utc)
    with sf.begin() as session:
        session.query(LedgerAccountModel).delete()
        session.query(CanonicalEscrow).delete()
        session.add_all([
            LedgerAccountModel(account_id="R-SOURCE", currency="MNT", balance=0, version=0, updated_at=now),
            LedgerAccountModel(account_id="R-ESCROW", currency="MNT", balance=100, version=0, updated_at=now),
            LedgerAccountModel(account_id="R-OTHER", currency="MNT", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="ea35-refund-escrow", sender_address="R-SOURCE", receiver_address="R-BEN",
                amount=100, state=EscrowState.LOCKED.value, condition_desc="refund proof",
                refund_destination="R-SOURCE", currency="MNT", version=2,
                created_at=now, updated_at=now,
            ),
        ])
    with sf.begin() as session:
        result = refund_escrow_in_transaction(
            session, transaction_id="EA35-REFUND-1", escrow_id="ea35-refund-escrow",
            amount=100, currency="MNT", payload={"requested_destination": "R-OTHER"},
        )
        assert result["replayed"] is False
    with sf() as session:
        assert session.get(LedgerAccountModel, "R-SOURCE").balance == 100
        assert session.get(LedgerAccountModel, "R-OTHER").balance == 0
        assert session.get(CanonicalEscrow, "ea35-refund-escrow").state == EscrowState.REFUNDED.value


def test_postgresql_funded_cancel_reverses_to_original_sender(factory):
    factory.create()
    sf = factory.session_factory
    now = datetime.now(timezone.utc)
    with sf.begin() as session:
        session.query(LedgerAccountModel).delete()
        session.query(CanonicalEscrow).delete()
        session.add_all([
            LedgerAccountModel(account_id="C-SOURCE", currency="MNT", balance=0, version=0, updated_at=now),
            LedgerAccountModel(account_id="C-ESCROW", currency="MNT", balance=100, version=0, updated_at=now),
            CanonicalEscrow(
                id="ea35-cancel-escrow", sender_address="C-SOURCE", receiver_address="C-BEN",
                amount=100, state=EscrowState.FUNDED.value, condition_desc="cancel proof",
                refund_destination="C-SOURCE", currency="MNT", version=1,
                created_at=now, updated_at=now,
            ),
        ])
    with sf.begin() as session:
        result = cancel_escrow_in_transaction(
            session, transaction_id="EA35-CANCEL-1", escrow_id="ea35-cancel-escrow",
        )
        assert result["replayed"] is False
    with sf() as session:
        assert session.get(LedgerAccountModel, "C-SOURCE").balance == 100
        assert session.get(LedgerAccountModel, "C-ESCROW").balance == 0
        assert session.get(CanonicalEscrow, "ea35-cancel-escrow").state == EscrowState.CANCELLED.value
