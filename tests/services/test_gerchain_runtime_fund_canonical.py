from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel
from persistence.atomic_value_transaction import WitnessBase, TransactionWitness
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase, CanonicalEscrow, EscrowState
from persistence.recovery_outbox import OutboxBase
from services.gerchain_runtime import GerchainRuntime


def test_production_runtime_fund_uses_canonical_ledger_and_durable_escrow():
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
            LedgerAccountModel(account_id="alice", currency="USD", balance=100, version=0, updated_at=now),
            LedgerAccountModel(account_id="escrow-1", currency="USD", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="escrow-1", sender_address="alice", receiver_address="bob",
                amount=40, state=EscrowState.CREATED.value, condition_desc=None,
                refund_destination="alice", currency="USD", version=0,
                created_at=now, updated_at=now,
            ),
        ])

    runtime = GerchainRuntime(
        escrow_id="escrow-1", amount=40, currency="USD", witness_id="w-1"
    )
    runtime.configure_canonical_ledger(sf)
    result = runtime.fund("fund-1", "alice", "T0", {"evidence": "ok"})

    assert result["replayed"] is False
    with sf() as session:
        assert session.get(LedgerAccountModel, "alice").balance == 60
        assert session.get(LedgerAccountModel, "escrow-1").balance == 40
        assert session.get(CanonicalEscrow, "escrow-1").state == "FUNDED"
        assert session.query(TransactionWitness).count() == 1

    engine.dispose()
