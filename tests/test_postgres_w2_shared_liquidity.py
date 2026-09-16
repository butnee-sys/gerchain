import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from persistence.atomic_release import (
    PostgreSQLAtomicRelease,
    ReleaseAccount,
    ReleaseEscrow,
    ReleaseOperation,
    ReleaseWitness,
    initialize_atomic_release_schema,
)


GOVERNANCE = {
    "decision_status": "APPROVE",
    "authorization_status": "AUTHORIZED",
    "trinity_proof": {"trust": True, "transparency": True, "performance": True},
    "evidence_verified": True,
}


@pytest.mark.integration
def test_distinct_concurrent_operations_share_one_canonical_liquidity_capacity():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL integration tests")

    engine = create_engine(url, pool_pre_ping=True, future=True, pool_size=20, max_overflow=20)
    initialize_atomic_release_schema(engine)
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    source = f"W2-LIQ-SRC-{suffix}"
    destinations = [f"W2-LIQ-DST-A-{suffix}", f"W2-LIQ-DST-B-{suffix}"]
    escrows = [f"W2-LIQ-ESC-A-{suffix}", f"W2-LIQ-ESC-B-{suffix}"]
    transactions = [f"W2-LIQ-TX-A-{suffix}", f"W2-LIQ-TX-B-{suffix}"]
    amount = 1_500_000
    capacity = 2_000_000

    with Session(engine) as session:
        now = datetime.now(timezone.utc)
        session.add(ReleaseAccount(account_id=source, balance=capacity, updated_at=now))
        for destination, escrow in zip(destinations, escrows):
            session.add(ReleaseAccount(account_id=destination, balance=0, updated_at=now))
            session.add(ReleaseEscrow(escrow_id=escrow, state="LOCKED", amount=amount, updated_at=now))
        session.commit()

    def attempt(index: int):
        service = PostgreSQLAtomicRelease(lambda: Session(engine))
        try:
            return service.release(
                idempotency_key=f"W2-LIQ-KEY-{index}-{suffix}",
                transaction_id=transactions[index],
                escrow_id=escrows[index],
                source=source,
                destination=destinations[index],
                amount=amount,
                **GOVERNANCE,
            )
        except Exception as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(attempt, i) for i in range(2)]
        results = [future.result() for future in as_completed(futures)]

    successes = [result for result in results if not isinstance(result, Exception) and not result.replay]
    failures = [result for result in results if isinstance(result, Exception)]
    assert len(successes) == 1
    assert len(failures) == 1

    with Session(engine) as session:
        source_row = session.get(ReleaseAccount, source)
        destination_rows = [session.get(ReleaseAccount, destination) for destination in destinations]
        released_escrows = [session.get(ReleaseEscrow, escrow) for escrow in escrows]
        operations = session.execute(
            select(ReleaseOperation).where(ReleaseOperation.transaction_id.in_(transactions))
        ).scalars().all()
        witnesses = session.execute(
            select(ReleaseWitness).where(ReleaseWitness.transaction_id.in_(transactions))
        ).scalars().all()

    committed = sum(destination.balance for destination in destination_rows)
    assert committed <= capacity
    assert source_row.balance == capacity - committed
    assert sum(escrow.state == "RELEASED" for escrow in released_escrows) == 1
    assert len(operations) == 1
    assert len(witnesses) == 1
    assert committed == amount
