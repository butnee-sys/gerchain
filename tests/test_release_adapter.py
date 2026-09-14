from __future__ import annotations

from unittest.mock import Mock

from persistence.atomic_release import AtomicReleaseResult
from persistence.release_adapter import PostgreSQLReleaseAdapter, ReleaseRequest


def test_release_adapter_forwards_authoritative_request():
    engine = Mock()
    engine.release.return_value = AtomicReleaseResult("TX-1", "ESC-1", "DST", 100)
    adapter = PostgreSQLReleaseAdapter(engine)
    request = ReleaseRequest(
        idempotency_key="KEY-1",
        transaction_id="TX-1",
        escrow_id="ESC-1",
        source="SRC",
        destination="DST",
        amount=100,
        decision_status="APPROVE",
        authorization_status="AUTHORIZED",
        trinity_proof={"trust": True, "transparency": True, "performance": True},
        evidence_verified=True,
    )
    result = adapter.execute(request)
    assert result.transaction_id == "TX-1"
    engine.release.assert_called_once_with(
        idempotency_key="KEY-1",
        transaction_id="TX-1",
        escrow_id="ESC-1",
        source="SRC",
        destination="DST",
        amount=100,
        decision_status="APPROVE",
        authorization_status="AUTHORIZED",
        trinity_proof={"trust": True, "transparency": True, "performance": True},
        evidence_verified=True,
    )
