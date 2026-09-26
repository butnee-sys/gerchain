from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel
from services.gerchain_runtime import GerchainRuntime

def test_production_runtime_settlement_uses_canonical_ledger():
    e=create_engine("sqlite+pysqlite:///:memory:")
    from persistence.atomic_value_transaction import WitnessBase
    from persistence.durable_idempotency import IdempotencyBase
    from persistence.recovery_outbox import OutboxBase
    AtomicLedgerBase.metadata.create_all(e)
    WitnessBase.metadata.create_all(e)
    IdempotencyBase.metadata.create_all(e)
    OutboxBase.metadata.create_all(e)
    sf=sessionmaker(bind=e)
    from datetime import datetime, timezone
    now=datetime.now(timezone.utc)
    with sf.begin() as s:
        s.add_all([
          LedgerAccountModel(account_id="A",currency="MNT",balance=100,version=0,updated_at=now),
          LedgerAccountModel(account_id="B",currency="MNT",balance=5,version=0,updated_at=now)
        ])
    r=GerchainRuntime(escrow_id="E",amount=10,currency="MNT",witness_id="w");r.configure_canonical_ledger(sf)
    out=r.settle(transaction_id="S1",source="A",destination="B",amount=30,currency="MNT")
    assert out["transaction_id"]=="S1"
    with sf() as s:
        assert s.get(LedgerAccountModel,"A").balance==70
        assert s.get(LedgerAccountModel,"B").balance==35
        assert s.query(LedgerMovementModel).count()==1
    e.dispose()


def test_settlement_binds_witness_outbox_and_idempotency():
    from persistence.atomic_value_transaction import TransactionWitness
    from persistence.durable_idempotency import DurableIdempotencyRecord
    from persistence.recovery_outbox import OutboxEvent
    e=create_engine("sqlite+pysqlite:///:memory:")
    from persistence.atomic_ledger import AtomicLedgerBase
    from persistence.atomic_value_transaction import WitnessBase
    from persistence.durable_idempotency import IdempotencyBase
    from persistence.recovery_outbox import OutboxBase
    AtomicLedgerBase.metadata.create_all(e); WitnessBase.metadata.create_all(e); IdempotencyBase.metadata.create_all(e); OutboxBase.metadata.create_all(e)
    sf=sessionmaker(bind=e)
    from datetime import datetime, timezone
    now=datetime.now(timezone.utc)
    with sf.begin() as s:
        s.add_all([LedgerAccountModel(account_id="A",currency="MNT",balance=100,version=0,updated_at=now), LedgerAccountModel(account_id="B",currency="MNT",balance=0,version=0,updated_at=now)])
    from persistence.settlement_coordinator import SettlementCoordinator
    with sf() as s:
        out=SettlementCoordinator(s).settle_in_transaction(transaction_id="S2",source="A",destination="B",amount=20,currency="MNT")
        s.commit()
        assert out["transaction_id"]=="S2"
        assert s.query(TransactionWitness).count()==1
        assert s.query(OutboxEvent).count()==1
        assert s.query(DurableIdempotencyRecord).count()==1
    e.dispose()
