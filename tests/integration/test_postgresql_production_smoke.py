import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.recovery_outbox import OutboxEvent
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_runtime_postgresql_full_escrow_lifecycle():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, future=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-smoke-escrow",
            amount=100,
            currency="MNT",
            witness_id="pg-smoke-witness",
        ),
        engine=engine,
    ).create()
    assert runtime.is_canonical_ledger_authoritative

    now = datetime.now(timezone.utc)
    with session_factory.begin() as session:
        session.add_all(
            [
                LedgerAccountModel(
                    account_id="pg-source",
                    currency="MNT",
                    balance=1000,
                    version=0,
                    updated_at=now,
                ),
                LedgerAccountModel(
                    account_id="pg-smoke-escrow",
                    currency="MNT",
                    balance=0,
                    version=0,
                    updated_at=now,
                ),
                LedgerAccountModel(
                    account_id="pg-beneficiary",
                    currency="MNT",
                    balance=0,
                    version=0,
                    updated_at=now,
                ),
                CanonicalEscrow(
                    id="pg-smoke-escrow",
                    sender_address="pg-source",
                    receiver_address="pg-beneficiary",
                    amount=100,
                    state=EscrowState.CREATED.value,
                    condition_desc="production-smoke",
                    refund_destination="pg-source",
                    currency="MNT",
                    version=0,
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )

    assert runtime.fund("pg-fund-1", "pg-source", "T0", {"verified": True})["replayed"] is False
    assert runtime.lock("pg-lock-1", "T1", {"verified": True})["replayed"] is False

    proof = {"trust": True, "transparency": True, "performance": True}
    assert runtime.release(
        transaction_id="pg-release-1",
        destination="pg-beneficiary",
        timestamp="T2",
        evidence={"verified": True},
        root=object(),
        owner_id="pg-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof=proof,
    )["replayed"] is False

    with session_factory() as session:
        source = session.get(LedgerAccountModel, "pg-source")
        escrow = session.get(LedgerAccountModel, "pg-smoke-escrow")
        beneficiary = session.get(LedgerAccountModel, "pg-beneficiary")
        aggregate = session.get(CanonicalEscrow, "pg-smoke-escrow")
        movements = session.execute(select(LedgerMovementModel)).scalars().all()
        witnesses = session.execute(select(TransactionWitness)).scalars().all()
        outbox = session.execute(select(OutboxEvent)).scalars().all()

        assert source.balance == 900
        assert escrow.balance == 0
        assert beneficiary.balance == 100
        assert aggregate.state == EscrowState.RELEASED.value
        assert [m.operation for m in movements] == ["FUND", "RELEASE"]
        assert len(movements) == 2
        assert {w.event_type for w in witnesses} == {"GERCHAIN_FUNDED", "GERCHAIN_LOCKED", "GERCHAIN_RELEASED"}
        assert len(witnesses) == 3
        assert {e.event_type for e in outbox} == {"GERCHAIN_FUNDED", "GERCHAIN_LOCKED", "GERCHAIN_RELEASED"}
        assert len(outbox) == 3

    # Release replay must not move value twice.
    replay = runtime.release(
        transaction_id="pg-release-1",
        destination="pg-beneficiary",
        timestamp="T2",
        evidence={"verified": True},
        root=object(),
        owner_id="pg-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof=proof,
    )
    assert replay["replayed"] is True

    with session_factory() as session:
        source = session.get(LedgerAccountModel, "pg-source")
        beneficiary = session.get(LedgerAccountModel, "pg-beneficiary")
        movements = session.execute(select(LedgerMovementModel)).scalars().all()
        assert source.balance == 900
        assert beneficiary.balance == 100
        assert len(movements) == 2

    # REFUND path: authoritative refund destination must win over caller input.
    refund_factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-refund-escrow",
            amount=50,
            currency="MNT",
            witness_id="pg-refund-witness",
        ),
        engine=engine,
    )
    refund_runtime = refund_factory.create()
    with session_factory.begin() as session:
        session.add_all([
            LedgerAccountModel(account_id="pg-refund-source", currency="MNT", balance=50, version=0, updated_at=now),
            LedgerAccountModel(account_id="pg-refund-escrow", currency="MNT", balance=0, version=0, updated_at=now),
            LedgerAccountModel(account_id="pg-refund-attacker", currency="MNT", balance=0, version=0, updated_at=now),
            CanonicalEscrow(id="pg-refund-escrow", sender_address="pg-refund-source", receiver_address="pg-refund-beneficiary", amount=50, state=EscrowState.CREATED.value, condition_desc="refund-smoke", refund_destination="pg-refund-source", currency="MNT", version=0, created_at=now, updated_at=now),
        ])
    refund_runtime.fund("pg-refund-fund", "pg-refund-source", "T0", {"verified": True})
    refund_runtime.lock("pg-refund-lock", "T1", {"verified": True})
    refund_runtime.refund(transaction_id="pg-refund-1", destination="pg-refund-attacker", timestamp="T2", evidence={"verified": True}, root=object(), owner_id="pg-owner", authorized=True, evidence_verified=True, trinity_proof=proof)
    replay_refund = refund_runtime.refund(transaction_id="pg-refund-1", destination="pg-refund-attacker", timestamp="T2", evidence={"verified": True}, root=object(), owner_id="pg-owner", authorized=True, evidence_verified=True, trinity_proof=proof)
    assert replay_refund["replayed"] is True
    assert refund_runtime.get_balance("pg-refund-source") == 50
    assert refund_runtime.get_balance("pg-refund-attacker") == 0
    with session_factory() as session:
        assert deep_reconcile_value_truth(session).matched

    # CANCEL path: CREATED cancellation is state-only; no value movement is allowed.
    cancel_factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(database_url=url, escrow_id="pg-cancel-escrow", amount=30, currency="MNT", witness_id="pg-cancel-witness"), engine=engine
    )
    cancel_runtime = cancel_factory.create()
    with session_factory.begin() as session:
        session.add(CanonicalEscrow(id="pg-cancel-escrow", sender_address="pg-cancel-source", receiver_address="pg-cancel-beneficiary", amount=30, state=EscrowState.CREATED.value, condition_desc="cancel-smoke", refund_destination="pg-cancel-source", currency="MNT", version=0, created_at=now, updated_at=now))
    cancel_runtime.cancel(transaction_id="pg-cancel-1", timestamp="T0", evidence={"verified": True})
    assert cancel_runtime.get_escrow_state()["state"] == EscrowState.CANCELLED.value
    with session_factory() as session:
        assert deep_reconcile_value_truth(session).matched

    # Settlement remains an orchestration path over the Canonical Ledger.
    settlement_factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(database_url=url, escrow_id="pg-settlement-escrow", amount=1, currency="MNT", witness_id="pg-settlement-witness"), engine=engine
    )
    settlement_runtime = settlement_factory.create()
    settlement_runtime.create_account("pg-settle-source", initial_balance=20)
    settlement_runtime.create_account("pg-settle-destination", initial_balance=0)
    settlement_runtime.settle(transaction_id="pg-settle-1", source="pg-settle-source", destination="pg-settle-destination", amount=7, currency="MNT")
    settlement_runtime.settle(transaction_id="pg-settle-1", source="pg-settle-source", destination="pg-settle-destination", amount=7, currency="MNT")
    assert settlement_runtime.get_balance("pg-settle-source") == 13
    assert settlement_runtime.get_balance("pg-settle-destination") == 7
    engine.dispose()
