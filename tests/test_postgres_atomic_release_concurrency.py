import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from persistence.atomic_release import PostgreSQLAtomicRelease, ReleaseAccount, ReleaseEscrow, ReleaseOperation, ReleaseWitness, initialize_atomic_release_schema


GOVERNANCE = {
    "decision_status": "APPROVE",
    "authorization_status": "AUTHORIZED",
    "trinity_proof": {"trust": True, "transparency": True, "performance": True},
    "evidence_verified": True,
}


@pytest.mark.integration
def test_100_concurrent_releases_exactly_one_wins():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL integration tests")

    engine = create_engine(url, pool_pre_ping=True, pool_size=20, max_overflow=80)
    initialize_atomic_release_schema(engine)
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        session.merge(ReleaseAccount(account_id="CONC-SRC", balance=2_000_000, updated_at=now))
        session.merge(ReleaseAccount(account_id="CONC-DST", balance=0, updated_at=now))
        session.merge(ReleaseEscrow(escrow_id="CONC-ESC", state="LOCKED", amount=2_000_000, updated_at=now))
        session.commit()

    def attempt(i: int):
        service = PostgreSQLAtomicRelease(lambda: Session(engine))
        try:
            return service.release(
                idempotency_key="CONC-RELEASE-001",
                transaction_id="CONC-TX-001",
                escrow_id="CONC-ESC",
                source="CONC-SRC",
                destination="CONC-DST",
                amount=2_000_000,
                **GOVERNANCE,
            )
        except Exception as exc:
            return exc

    with ThreadPoolExecutor(max_workers=100) as pool:
        results = list(pool.map(attempt, range(100)))

    with Session(engine) as session:
        source = session.get(ReleaseAccount, "CONC-SRC")
        destination = session.get(ReleaseAccount, "CONC-DST")
        escrow = session.get(ReleaseEscrow, "CONC-ESC")
        operations = session.execute(select(func.count(ReleaseOperation.id)).where(ReleaseOperation.idempotency_key == "CONC-RELEASE-001")).scalar_one()
        witnesses = session.execute(select(func.count(ReleaseWitness.id)).where(ReleaseWitness.transaction_id == "CONC-TX-001")).scalar_one()

    successes = [r for r in results if not isinstance(r, Exception) and not r.replay]
    replays = [r for r in results if not isinstance(r, Exception) and r.replay]
    assert len(successes) == 1
    assert len(replays) == 99
    assert source.balance == 0
    assert destination.balance == 2_000_000
    assert escrow.state == "RELEASED"
    assert operations == 1
    assert witnesses == 1
