from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase, CanonicalEscrow, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from services.gerchain_runtime import GerchainRuntime


def _setup():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    AtomicLedgerBase.metadata.create_all(engine)
    EscrowBase.metadata.create_all(engine)
    WitnessBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    OutboxBase.metadata.create_all(engine)
    sf = sessionmaker(bind=engine)
    now = datetime.now(timezone.utc)
    with sf.begin() as s:
        s.add_all([
            LedgerAccountModel(account_id="alice", currency="USD", balance=60, version=0, updated_at=now),
            LedgerAccountModel(account_id="escrow-1", currency="USD", balance=40, version=0, updated_at=now),
            CanonicalEscrow(
                id="escrow-1", sender_address="alice", receiver_address="bob",
                amount=40, state=EscrowState.FUNDED.value, condition_desc=None,
                refund_destination="alice", currency="USD", version=1,
                created_at=now, updated_at=now,
            ),
        ])
    return engine, sf


def test_production_lock_changes_only_durable_state_and_evidence():
    engine, sf = _setup()
    runtime = GerchainRuntime(
        escrow_id="escrow-1", amount=40, currency="USD", witness_id="w-1"
    )
    runtime.configure_canonical_ledger(sf)

    result = runtime.lock("lock-1", "T1", {"evidence": "ok"})
    assert result["replayed"] is False
    assert result["value_movement"] is False

    with sf() as s:
        assert s.get(CanonicalEscrow, "escrow-1").state == "LOCKED"
        assert s.get(LedgerAccountModel, "alice").balance == 60
        assert s.get(LedgerAccountModel, "escrow-1").balance == 40
        assert s.query(OutboxEvent).count() == 1
        assert s.query(TransactionWitness).count() == 1

    engine.dispose()
