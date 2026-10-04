from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase, CanonicalEscrow, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from services.gerchain_runtime import GerchainRuntime

def setup():
    e=create_engine("sqlite+pysqlite:///:memory:")
    for b in (AtomicLedgerBase,EscrowBase,WitnessBase,IdempotencyBase,OutboxBase): b.metadata.create_all(e)
    return e,sessionmaker(bind=e)

def test_funded_cancel_reverses_to_authoritative_sender():
    e,sf=setup(); now=datetime.now(timezone.utc)
    with sf.begin() as s:
        s.add_all([
          LedgerAccountModel(account_id="E1",currency="MNT",balance=40,version=1,updated_at=now),
          LedgerAccountModel(account_id="SRC",currency="MNT",balance=60,version=1,updated_at=now),
          LedgerAccountModel(account_id="OTHER",currency="MNT",balance=0,version=0,updated_at=now),
          CanonicalEscrow(id="E1",sender_address="SRC",receiver_address="BEN",amount=40,state=EscrowState.FUNDED.value,condition_desc="ok",refund_destination="SRC",currency="MNT",version=1,created_at=now,updated_at=now)
        ])
    r=GerchainRuntime(escrow_id="E1",amount=40,currency="MNT",witness_id="w");r.configure_canonical_ledger(sf)
    out=r.cancel(transaction_id="C1",timestamp="T4",evidence={"reason":"cancel"})
    assert out["replayed"] is False
    with sf() as s:
        assert s.get(LedgerAccountModel,"E1").balance==0
        assert s.get(LedgerAccountModel,"SRC").balance==100
        assert s.get(LedgerAccountModel,"OTHER").balance==0
        assert s.get(CanonicalEscrow,"E1").state=="CANCELLED"
        assert s.query(LedgerMovementModel).count()==1
        assert s.query(TransactionWitness).count()==1
        assert s.query(OutboxEvent).count()==1
    e.dispose()

def test_created_cancel_is_state_only():
    e,sf=setup(); now=datetime.now(timezone.utc)
    with sf.begin() as s:
        s.add(CanonicalEscrow(id="E1",sender_address="SRC",receiver_address="BEN",amount=40,state=EscrowState.CREATED.value,condition_desc="ok",refund_destination="SRC",currency="MNT",version=0,created_at=now,updated_at=now))
    r=GerchainRuntime(escrow_id="E1",amount=40,currency="MNT",witness_id="w");r.configure_canonical_ledger(sf)
    out=r.cancel(transaction_id="C2",timestamp="T4",evidence={})
    assert out["replayed"] is False
    with sf() as s:
        assert s.get(CanonicalEscrow,"E1").state=="CANCELLED"
        assert s.query(LedgerMovementModel).count()==0
    e.dispose()
