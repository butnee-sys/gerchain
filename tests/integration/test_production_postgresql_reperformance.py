import os
import base64
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel
from persistence.atomic_value_transaction import WitnessBase, TransactionWitness
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase, CanonicalEscrow, EscrowState
from persistence.recovery_outbox import OutboxBase
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory
from dee_security.root_of_trust import RootOfTrust


def test_postgresql_production_runtime_boot_and_value_truth():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    sf = sessionmaker(bind=engine, expire_on_commit=False)
    for base in (AtomicLedgerBase, EscrowBase, WitnessBase, IdempotencyBase, OutboxBase):
        base.metadata.create_all(engine)

    now = datetime.now(timezone.utc)
    with sf.begin() as session:
        session.add_all([
            LedgerAccountModel(account_id="pg-alice", currency="USD", balance=100, version=0, updated_at=now),
            LedgerAccountModel(account_id="pg-escrow-1", currency="USD", balance=0, version=0, updated_at=now),
            LedgerAccountModel(account_id="pg-bob", currency="USD", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="pg-escrow-1", sender_address="pg-alice", receiver_address="pg-bob",
                amount=40, state=EscrowState.CREATED.value, condition_desc=None,
                refund_destination="pg-alice", currency="USD", version=0,
                created_at=now, updated_at=now,
            ),
        ])

    factory = ProductionRuntimeFactory(ProductionRuntimeConfig(
        database_url=url, escrow_id="pg-escrow-1", amount=40,
        currency="USD", witness_id="pg-w-1",
    ), engine=engine)
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    funded = runtime.fund("pg-fund-1", "pg-alice", "T0", {"evidence": "ok"})
    assert funded["replayed"] is False
    runtime.lock("pg-lock-1", "T1", {"evidence": "ok"})
    released = runtime.release(
        root=RootOfTrust("pg-owner", base64.b64encode(bytes(32)).decode("ascii")),
        owner_id="pg-owner",
        transaction_id="pg-release-1",
        destination="pg-bob",
        authorized=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
        evidence_verified=True,
        timestamp="T2",
        evidence={"evidence": "ok"},
    )
    assert released["replayed"] is False

    with sf() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, [f"{i.code}:{i.transaction_id}:{i.detail}" for i in report.issues]
        assert session.get(LedgerAccountModel, "pg-alice").balance == 60
        assert session.get(LedgerAccountModel, "pg-escrow-1").balance == 0
        assert session.get(LedgerAccountModel, "pg-bob").balance == 40
        assert session.get(CanonicalEscrow, "pg-escrow-1").state == EscrowState.RELEASED.value
        assert session.query(TransactionWitness).count() == 3

    engine.dispose()
