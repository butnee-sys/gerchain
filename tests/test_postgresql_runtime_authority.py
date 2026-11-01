from __future__ import annotations

import pytest

from services.gerchain_runtime import GerchainRuntime


def test_memory_runtime_is_explicitly_test_only() -> None:
    runtime = GerchainRuntime(
        escrow_id="ESC-TEST",
        amount=100,
        currency="NEF",
        witness_id="W-TEST",
    )

    assert runtime.runtime_mode == "test-memory"
    assert runtime.is_postgresql_authoritative is False
    with pytest.raises(RuntimeError, match="PostgreSQL authoritative runtime"):
        runtime.require_postgresql_authority()


def test_legacy_postgresql_release_authority_is_disabled() -> None:
    runtime = GerchainRuntime(
        escrow_id="ESC-TEST-2",
        amount=100,
        currency="NEF",
        witness_id="W-TEST-2",
    )

    with pytest.raises(RuntimeError, match="legacy PostgreSQL release adapter is disabled"):
        runtime.configure_postgres_release(lambda: None)

    assert runtime.runtime_mode == "test-memory"
    assert runtime.is_postgresql_authoritative is False
