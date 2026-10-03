from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase
from persistence.atomic_value_transaction import TransactionWitness
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.release_escrow import release_escrow_in_transaction
from persistence.recovery_outbox import OutboxBase


def _factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    AtomicLedgerBase.metadata.create_all(engine)
    EscrowBase.metadata.create_all(engine)
    OutboxBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    TransactionWitness.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)


def test_release_cannot_redirect_authoritative_beneficiary():
    engine, factory = _factory()
    with factory() as session:
        now = datetime.now(timezone.utc)
        session.add(CanonicalEscrow(
            id="esc-release",
            sender_address="SRC",
            receiver_address="BENEFICIARY",
            amount=10,
            state=EscrowState.LOCKED.value,
            condition_desc="test",
            refund_destination="SRC",
            currency="USD",
            version=1,
            created_at=now,
            updated_at=now,
        ))
        session.commit()

        with pytest.raises(ValueError, match="authoritative escrow beneficiary"):
            release_escrow_in_transaction(
                session,
                transaction_id="tx-release-redirect",
                escrow_id="esc-release",
                beneficiary="ATTACKER",
                amount=10,
                currency="USD",
                decision_status="APPROVE",
                authorization_status="AUTHORIZED",
                trust=True,
                transparency=True,
                performance=True,
                evidence_verified=True,
            )

        assert session.get(CanonicalEscrow, "esc-release").state == EscrowState.LOCKED.value
        assert session.query(TransactionWitness).count() == 0
    engine.dispose()
