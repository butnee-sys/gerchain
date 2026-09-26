from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase, CanonicalEscrow, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from services.gerchain_runtime import GerchainRuntime


def test_production_runtime_release_uses_canonical_ledger():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    AtomicLedgerBase.metadata.create_all(engine)
    EscrowBase.metadata.create_all(engine)
    WitnessBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    OutboxBase.metadata.create_all(engine)
    sf = sessionmaker(bind=engine)
    now = datetime.now(timezone.utc)

    with sf.begin() as session:
        session.add_all([
            LedgerAccountModel(account_id="escrow-1", currency="USD", balance=40, version=1, updated_at=now),
            LedgerAccountModel(account_id="bob", currency="USD", balance=10, version=0, updated_at=now),
            CanonicalEscrow(
                id="escrow-1", sender_address="alice", receiver_address="bob",
                amount=40, state=EscrowState.LOCKED.value, condition_desc=None,
                refund_destination="alice", currency="USD", version=2,
                created_at=now, updated_at=now,
            ),
        ])

    runtime = GerchainRuntime(
        escrow_id="escrow-1", amount=40, currency="USD", witness_id="w-1"
    )
    runtime.configure_canonical_ledger(sf)

    result = runtime.release(
        transaction_id="release-1",
        destination="bob",
        timestamp="T2",
        evidence={"evidence": "verified"},
        root=object(),
        owner_id="owner-1",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
        source="alice",
    )

    assert result["replayed"] is False
    with sf() as session:
        assert session.get(LedgerAccountModel, "escrow-1").balance == 0
        assert session.get(LedgerAccountModel, "bob").balance == 50
        assert session.get(CanonicalEscrow, "escrow-1").state == "RELEASED"
        assert session.query(LedgerMovementModel).count() == 1
        assert session.query(TransactionWitness).count() == 1
        assert session.query(OutboxEvent).count() == 1

    engine.dispose()
