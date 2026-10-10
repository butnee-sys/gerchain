from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import select

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def _seed_escrow(factory, escrow_id: str, *, sender: str, receiver: str, amount: int = 10):
    now = datetime.now(timezone.utc)
    with factory.session_factory() as session:
        session.add(
            CanonicalEscrow(
                id=escrow_id,
                sender_address=sender,
                receiver_address=receiver,
                amount=amount,
                state=EscrowState.CREATED.value,
                condition_desc="postgres-production-e2e",
                refund_destination=sender,
                currency="USD",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()


def _account_balance(factory, account_id: str) -> int:
    with factory.session_factory() as session:
        row = session.execute(
            select(LedgerAccountModel).where(LedgerAccountModel.account_id == account_id)
        ).scalar_one()
        return int(row.balance)


def test_production_postgresql_runtime_full_value_flow():
    database_url = os.environ["GERCHAIN_TEST_DATABASE_URL"]
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="e2e-release",
            amount=10,
            currency="USD",
            witness_id="witness-production-e2e",
        )
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    accounts = {
        "sender-release": 100,
        "e2e-release": 0,
        "receiver-release": 0,
        "sender-refund": 100,
        "e2e-refund": 0,
        "receiver-refund": 0,
        "sender-cancel": 100,
        "e2e-cancel": 0,
        "receiver-cancel": 0,
        "settlement-source": 100,
        "settlement-destination": 0,
    }
    for account_id, balance in accounts.items():
        runtime.create_account(account_id, balance)

    _seed_escrow(factory, "e2e-release", sender="sender-release", receiver="receiver-release")
    _seed_escrow(factory, "e2e-refund", sender="sender-refund", receiver="receiver-refund")
    _seed_escrow(factory, "e2e-cancel", sender="sender-cancel", receiver="receiver-cancel")

    runtime.fund("e2e-release-fund", "sender-release", "t1", {"kind": "fund"})
    runtime.lock("e2e-release-lock", "t2", {"kind": "lock"})
    runtime.release(
        transaction_id="e2e-release-value",
        destination="receiver-release",
        timestamp="t3",
        evidence={"kind": "release"},
        root=object(),
        owner_id="production-e2e",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )

    refund_runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="e2e-refund",
            amount=10,
            currency="USD",
            witness_id="witness-production-e2e-refund",
        )
    ).create()
    refund_runtime.fund("e2e-refund-fund", "sender-refund", "t4", {"kind": "fund"})
    refund_runtime.lock("e2e-refund-lock", "t5", {"kind": "lock"})
    refund_runtime.refund(
        transaction_id="e2e-refund-value",
        destination="attacker",
        timestamp="t6",
        evidence={"kind": "refund"},
        root=object(),
        owner_id="production-e2e",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )

    cancel_runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="e2e-cancel",
            amount=10,
            currency="USD",
            witness_id="witness-production-e2e-cancel",
        )
    ).create()
    cancel_runtime.fund("e2e-cancel-fund", "sender-cancel", "t7", {"kind": "fund"})
    cancel_runtime.cancel(transaction_id="e2e-cancel-value", timestamp="t8", evidence={"kind": "cancel"})

    runtime.settle(
        transaction_id="e2e-settlement",
        source="settlement-source",
        destination="settlement-destination",
        amount=10,
        currency="USD",
    )

    assert runtime.get_escrow_state()["state"] == EscrowState.RELEASED.value
    assert refund_runtime.get_escrow_state()["state"] == EscrowState.REFUNDED.value
    assert cancel_runtime.get_escrow_state()["state"] == EscrowState.CANCELLED.value

    assert _account_balance(factory, "receiver-release") == 10
    assert _account_balance(factory, "sender-refund") == 100
    assert _account_balance(factory, "settlement-destination") == 10

    with factory.session_factory() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues
