import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from persistence.atomic_release import ReleaseAccount, ReleaseEscrow, PostgreSQLAtomicRelease, initialize_atomic_release_schema
from persistence.governed_atomic_release import GovernedAtomicRelease, ReleaseGovernance, ReleaseGovernanceError


@pytest.fixture()
def governed_release():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL integration tests")
    engine = create_engine(url, pool_pre_ping=True)
    initialize_atomic_release_schema(engine)
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        session.add_all([
            ReleaseAccount(account_id="GOV-SRC", balance=2_000_000, updated_at=now),
            ReleaseAccount(account_id="GOV-DST", balance=0, updated_at=now),
            ReleaseEscrow(escrow_id="GOV-ESC", state="LOCKED", amount=2_000_000, updated_at=now),
        ])
        session.commit()
    return GovernedAtomicRelease(PostgreSQLAtomicRelease(lambda: Session(engine)))


def good_governance():
    return ReleaseGovernance(
        decision="APPROVE",
        authorization="AUTHORIZED",
        trust="PASS",
        transparency="PASS",
        performance="PASS",
        evidence_verified=True,
    )


def test_governed_release_passes_all_gates(governed_release):
    result = governed_release.release(
        governance=good_governance(), idempotency_key="GOV-1", transaction_id="GOV-TX-1",
        escrow_id="GOV-ESC", source="GOV-SRC", destination="GOV-DST", amount=2_000_000,
    )
    assert result.replay is False


@pytest.mark.parametrize("field,value", [
    ("decision", "DENY"),
    ("authorization", "DENIED"),
    ("trust", "FAIL"),
    ("transparency", "FAIL"),
    ("performance", "FAIL"),
])
def test_governance_failure_blocks_value_movement(governed_release, field, value):
    data = good_governance().__dict__.copy()
    data[field] = value
    with pytest.raises(ReleaseGovernanceError):
        governed_release.release(
            governance=ReleaseGovernance(**data), idempotency_key=f"GOV-{field}", transaction_id=f"GOV-TX-{field}",
            escrow_id="GOV-ESC", source="GOV-SRC", destination="GOV-DST", amount=2_000_000,
        )
