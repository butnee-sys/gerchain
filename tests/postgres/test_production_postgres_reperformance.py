import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel, PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import WitnessBase, TransactionWitness
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase, CanonicalEscrow, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


@pytest.mark.postgres
def test_production_postgres_factory_and_canonical_value_flow():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-smoke-escrow",
            amount=100,
            currency="MNT",
            witness_id="pg-smoke-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    for base in (AtomicLedgerBase, EscrowBase, OutboxBase, IdempotencyBase, WitnessBase):
        base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)
    with Session() as session:
        for account_id, balance in (("pg-smoke-source", 100), ("pg-smoke-escrow", 0), ("pg-smoke-beneficiary", 0)):
            session.add(LedgerAccountModel(
                account_id=account_id, currency="MNT", balance=balance, version=0, updated_at=now
            ))
        session.add(CanonicalEscrow(
            id="pg-smoke-escrow",
            sender_address="pg-smoke-source",
            receiver_address="pg-smoke-beneficiary",
            refund_destination="pg-smoke-source",
            amount=100,
            state=EscrowState.CREATED.value,
            condition_desc="postgres-smoke",
            currency="MNT",
            version=0,
            created_at=now,
            updated_at=now,
        ))
        session.commit()

        fund_escrow_in_transaction(
            session, transaction_id="pg-smoke-fund", escrow_id="pg-smoke-escrow",
            source="pg-smoke-source", amount=100, currency="MNT",
        )
        session.commit()

        lock_escrow_in_transaction(
            session, transaction_id="pg-smoke-lock", escrow_id="pg-smoke-escrow"
        )
        session.commit()

        release_escrow_in_transaction(
            session, transaction_id="pg-smoke-release", escrow_id="pg-smoke-escrow",
            beneficiary="pg-smoke-beneficiary", amount=100, currency="MNT",
            decision_status="APPROVE", authorization_status="AUTHORIZED",
            trust=True, transparency=True, performance=True, evidence_verified=True,
        )
        session.commit()

        escrow = session.execute(select(CanonicalEscrow).where(CanonicalEscrow.id == "pg-smoke-escrow")).scalar_one()
        balances = {
            row.account_id: row.balance
            for row in session.execute(select(LedgerAccountModel)).scalars()
            if row.account_id.startswith("pg-smoke-")
        }
        movements = session.execute(
            select(LedgerMovementModel).where(LedgerMovementModel.transaction_id.in_(
                ["pg-smoke-fund", "pg-smoke-release"]
            ))
        ).scalars().all()
        witnesses = session.execute(select(TransactionWitness)).scalars().all()
        outbox = session.execute(select(OutboxEvent)).scalars().all()

        assert escrow.state == EscrowState.RELEASED.value
        assert balances == {
            "pg-smoke-source": 0,
            "pg-smoke-escrow": 0,
            "pg-smoke-beneficiary": 100,
        }
        assert len(movements) == 2
        assert {w.event_type for w in witnesses} >= {"GERCHAIN_FUNDED", "GERCHAIN_LOCKED", "GERCHAIN_RELEASED"}
        assert {e.event_type for e in outbox} >= {"GERCHAIN_FUNDED", "GERCHAIN_LOCKED", "GERCHAIN_RELEASED"}

    engine.dispose()
