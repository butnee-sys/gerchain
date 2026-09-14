import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from persistence.atomic_release import ReleaseAccount, ReleaseEscrow, ReleaseOperation, ReleaseWitness, PostgreSQLAtomicRelease, initialize_atomic_release_schema
from persistence.governed_atomic_release import GovernedAtomicRelease, ReleaseGovernance
from persistence.recovery_outbox import OutboxEvent


@pytest.fixture()
def release_fixture():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL integration tests")
    engine = create_engine(url, pool_pre_ping=True, future=True)
    initialize_atomic_release_schema(engine)
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    source = f"CONC-SRC-{suffix}"
    destination = f"CONC-DST-{suffix}"
    escrow_id = f"CONC-ESC-{suffix}"
    transaction_id = f"CONC-TX-{suffix}"
    with Session(engine) as session:
        now = datetime.now(timezone.utc)
        session.add_all([
            ReleaseAccount(account_id=source, balance=2_000_000, updated_at=now),
            ReleaseAccount(account_id=destination, balance=0, updated_at=now),
            ReleaseEscrow(escrow_id=escrow_id, state="LOCKED", amount=2_000_000, updated_at=now),
        ])
        session.commit()
    governed = GovernedAtomicRelease(PostgreSQLAtomicRelease(lambda: Session(engine)))
    return engine, governed, source, destination, escrow_id, transaction_id


def governance():
    return ReleaseGovernance(decision="APPROVE", authorization="AUTHORIZED", trust="PASS", transparency="PASS", performance="PASS", evidence_verified=True)


def test_100_concurrent_same_release_moves_value_once(release_fixture):
    engine, governed, source, destination, escrow_id, transaction_id = release_fixture

    def invoke(_index):
        return governed.release(governance=governance(), idempotency_key="CONC-SAME-KEY", transaction_id=transaction_id, escrow_id=escrow_id, source=source, destination=destination, amount=2_000_000)

    results = []
    errors = []
    with ThreadPoolExecutor(max_workers=100) as pool:
        futures = [pool.submit(invoke, i) for i in range(100)]
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                errors.append(exc)

    assert not errors
    assert len(results) == 100
    assert sum(not result.replay for result in results) == 1
    assert sum(result.replay for result in results) == 99

    with Session(engine) as session:
        src = session.get(ReleaseAccount, source)
        dst = session.get(ReleaseAccount, destination)
        escrow = session.get(ReleaseEscrow, escrow_id)
        operations = session.execute(select(ReleaseOperation).where(ReleaseOperation.idempotency_key == "CONC-SAME-KEY")).scalars().all()
        witnesses = session.execute(select(ReleaseWitness).where(ReleaseWitness.transaction_id == transaction_id)).scalars().all()
        events = session.execute(select(OutboxEvent).where(OutboxEvent.event_id == f"release:{transaction_id}")).scalars().all()

    assert src.balance == 0
    assert dst.balance == 2_000_000
    assert escrow.state == "RELEASED"
    assert len(operations) == 1
    assert len(witnesses) == 1
    assert len(events) == 1
    assert events[0].state == "PENDING"


def test_same_idempotency_key_with_different_transaction_is_conflict(release_fixture):
    engine, governed, source, destination, escrow_id, transaction_id = release_fixture
    governed.release(governance=governance(), idempotency_key="CONC-CONFLICT-KEY", transaction_id=transaction_id, escrow_id=escrow_id, source=source, destination=destination, amount=2_000_000)

    with pytest.raises(Exception, match="idempotency conflict"):
        governed.release(governance=governance(), idempotency_key="CONC-CONFLICT-KEY", transaction_id=f"{transaction_id}-OTHER", escrow_id=escrow_id, source=source, destination=destination, amount=2_000_000)
