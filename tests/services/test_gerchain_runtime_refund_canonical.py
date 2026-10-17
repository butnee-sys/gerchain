from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase, CanonicalEscrow, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from services.gerchain_runtime import GerchainRuntime

def test_production_runtime_refund_uses_authoritative_refund_destination():
    engine=create_engine("sqlite+pysqlite:///:memory:")
    for base in (AtomicLedgerBase, EscrowBase, WitnessBase, IdempotencyBase, OutboxBase):
        base.metadata.create_all(engine)
    sf=sessionmaker(bind=engine); now=datetime.now(timezone.utc)
    with sf.begin() as s:
        s.add_all([
            LedgerAccountModel(account_id="E1",currency="MNT",balance=40,version=1,updated_at=now),
            LedgerAccountModel(account_id="SRC",currency="MNT",balance=0,version=0,updated_at=now),
            LedgerAccountModel(account_id="ATTACKER",currency="MNT",balance=0,version=0,updated_at=now),
            CanonicalEscrow(id="E1",sender_address="SRC",receiver_address="BEN",amount=40,state=EscrowState.LOCKED.value,condition_desc="ok",refund_destination="SRC",currency="MNT",version=2,created_at=now,updated_at=now),
        ])
    r=GerchainRuntime(escrow_id="E1",amount=40,currency="MNT",witness_id="w")
    r.configure_canonical_ledger(sf)
    out=r.refund(transaction_id="RF1",destination="ATTACKER",timestamp="T3",evidence={"verified":True},root=object(),owner_id="owner",authorized=True,evidence_verified=True,trinity_proof={"trust":True,"transparency":True,"performance":True})
    assert out["replayed"] is False
    with sf() as s:
        assert s.get(LedgerAccountModel,"E1").balance==0
        assert s.get(LedgerAccountModel,"SRC").balance==40
        assert s.get(LedgerAccountModel,"ATTACKER").balance==0
        assert s.get(CanonicalEscrow,"E1").state=="REFUNDED"
        assert s.query(LedgerMovementModel).count()==1
        assert s.query(TransactionWitness).count()==1
        assert s.query(OutboxEvent).count()==1
    engine.dispose()
