from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import DurableIdempotencyRecord, IdempotencyBase
from persistence.escrow_aggregate import (
    CanonicalEscrow,
    EscrowBase,
    EscrowState,
    create_escrow_in_transaction,
)
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from services.gerchain_runtime import GerchainRuntime


def test_canonical_runtime_create_fund_lock_release_is_one_consistent_evidence_graph():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    AtomicLedgerBase.metadata.create_all(engine)
    EscrowBase.metadata.create_all(engine)
    WitnessBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    OutboxBase.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    now = datetime.now(timezone.utc)

    with factory.begin() as session:
        session.add_all([
            LedgerAccountModel(
                account_id="alice", currency="MNT", balance=100,
                version=0, updated_at=now,
            ),
            LedgerAccountModel(
                account_id="escrow-atomic-1", currency="MNT", balance=0,
                version=0, updated_at=now,
            ),
            LedgerAccountModel(
                account_id="bob", currency="MNT", balance=0,
                version=0, updated_at=now,
            ),
        ])
        create_escrow_in_transaction(
            session,
            escrow_id="escrow-atomic-1",
            sender="alice",
            beneficiary="bob",
            refund_destination="alice",
            amount=40,
            currency="MNT",
            condition="all canonical gates pass",
        )

    runtime = GerchainRuntime(
        escrow_id="escrow-atomic-1",
        amount=40,
        currency="MNT",
        witness_id="witness-atomic-1",
    )
    runtime.configure_canonical_ledger(factory)

    funded = runtime.fund("atomic-fund-1", "alice", "T1", {"evidence": "funded"})
    locked = runtime.lock("atomic-lock-1", "T2", {"evidence": "locked"})
    released = runtime.release(
        transaction_id="atomic-release-1",
        destination="bob",
        timestamp="T3",
        evidence={"evidence": "release-verified"},
        root=object(),
        owner_id="owner-1",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
        source="escrow-atomic-1",
    )

    assert funded["replayed"] is False
    assert locked["replayed"] is False
    assert released["replayed"] is False
    assert runtime.get_balance("alice") == 60
    assert runtime.get_balance("escrow-atomic-1") == 0
    assert runtime.get_balance("bob") == 40
    assert runtime.get_escrow_state()["state"] == EscrowState.RELEASED.value

    with factory() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, [issue.__dict__ for issue in report.issues]
        assert session.execute(select(LedgerMovementModel)).scalars().all()
        assert session.query(LedgerMovementModel).count() == 2
        assert session.query(TransactionWitness).count() == 3
        assert session.query(OutboxEvent).count() == 3
        assert session.query(DurableIdempotencyRecord).count() == 3
        escrow = session.get(CanonicalEscrow, "escrow-atomic-1")
        assert escrow is not None and escrow.state == EscrowState.RELEASED.value
        assert session.query(LedgerAccountModel).count() == 3

    engine.dispose()
