from unittest.mock import Mock

from services.gerchain_runtime import GerchainRuntime
from persistence.atomic_release import AtomicReleaseResult
from persistence.release_adapter import ReleaseRequest


def test_runtime_can_attach_durable_release_without_replacing_default():
    runtime = GerchainRuntime(escrow_id="RUNTIME-ESC", amount=100, currency="MNT", witness_id="RUNTIME-W")
    engine = Mock()
    engine.release.return_value = AtomicReleaseResult("RUNTIME-TX", "RUNTIME-ESC", "DST", 100)

    adapter = runtime.configure_postgres_release(lambda: None)
    adapter.release_engine = engine
    result = runtime.release_postgres(ReleaseRequest(
        idempotency_key="RUNTIME-K",
        transaction_id="RUNTIME-TX",
        escrow_id="RUNTIME-ESC",
        source="SRC",
        destination="DST",
        amount=100,
        decision_status="APPROVE",
        authorization_status="AUTHORIZED",
        trinity_proof={"trust": True, "transparency": True, "performance": True},
        evidence_verified=True,
    ))
    assert result.transaction_id == "RUNTIME-TX"
