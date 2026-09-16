import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from core.economic_state import EconomicStateFingerprint
from persistence.atomic_release import (
    PostgreSQLAtomicRelease,
    ReleaseAccount,
    ReleaseEscrow,
    ReleaseOperation,
    ReleaseWitness,
    initialize_atomic_release_schema,
)
from persistence.decision_bound_release import (
    DecisionBoundPostgreSQLRelease,
    StaleDecisionError,
    release_decision_state,
)


GOVERNANCE = {
    "decision_status": "APPROVE",
    "authorization_status": "AUTHORIZED",
    "trinity_proof": {"trust": True, "transparency": True, "performance": True},
    "evidence_verified": True,
}


@pytest.mark.integration
def test_changed_relevant_state_rejects_stale_decision_without_economic_mutation():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL integration tests")

    engine = create_engine(url, pool_pre_ping=True, future=True)
    initialize_atomic_release_schema(engine)
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    source = f"W2-STALE-SRC-{suffix}"
    destination = f"W2-STALE-DST-{suffix}"
    escrow_id = f"W2-STALE-ESC-{suffix}"
    transaction_id = f"W2-STALE-TX-{suffix}"
    amount = 1_000_000

    with Session(engine) as session:
        now = datetime.now(timezone.utc)
        session.add_all([
            ReleaseAccount(account_id=source, balance=2_000_000, updated_at=now),
            ReleaseAccount(account_id=destination, balance=0, updated_at=now),
            ReleaseEscrow(escrow_id=escrow_id, state="LOCKED", amount=amount, updated_at=now),
        ])
        session.commit()

    with Session(engine) as session:
        source_row = session.get(ReleaseAccount, source)
        escrow_row = session.get(ReleaseEscrow, escrow_id)
        assert source_row is not None
        assert escrow_row is not None
        decision_state: EconomicStateFingerprint = release_decision_state(
            source=source_row,
            escrow=escrow_row,
            amount=amount,
        ).fingerprint

    with Session(engine) as session:
        source_row = session.get(ReleaseAccount, source)
        assert source_row is not None
        source_row.balance = 500_000
        source_row.updated_at = datetime.now(timezone.utc)
        session.commit()

    guarded = DecisionBoundPostgreSQLRelease(PostgreSQLAtomicRelease(lambda: Session(engine)))
    with pytest.raises(StaleDecisionError, match="decision is stale"):
        guarded.release(
            decision_state=decision_state,
            idempotency_key=f"W2-STALE-KEY-{suffix}",
            transaction_id=transaction_id,
            escrow_id=escrow_id,
            source=source,
            destination=destination,
            amount=amount,
            **GOVERNANCE,
        )

    with Session(engine) as session:
        source_row = session.get(ReleaseAccount, source)
        destination_row = session.get(ReleaseAccount, destination)
        escrow_row = session.get(ReleaseEscrow, escrow_id)
        operations = session.execute(
            select(ReleaseOperation).where(ReleaseOperation.transaction_id == transaction_id)
        ).scalars().all()
        witnesses = session.execute(
            select(ReleaseWitness).where(ReleaseWitness.transaction_id == transaction_id)
        ).scalars().all()

    assert source_row.balance == 500_000
    assert destination_row.balance == 0
    assert escrow_row.state == "LOCKED"
    assert operations == []
    assert witnesses == []
