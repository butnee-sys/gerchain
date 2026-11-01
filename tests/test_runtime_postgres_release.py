from __future__ import annotations

import pytest

from services.gerchain_runtime import GerchainRuntime


def test_runtime_rejects_legacy_boolean_authorized_postgres_release_path():
    runtime = GerchainRuntime(
        escrow_id="RUNTIME-ESC",
        amount=100,
        currency="MNT",
        witness_id="RUNTIME-W",
    )
    with pytest.raises(RuntimeError, match="legacy PostgreSQL release adapter is disabled"):
        runtime.configure_postgres_release(lambda: None)
    with pytest.raises(RuntimeError, match="legacy PostgreSQL release adapter is disabled"):
        runtime.release_postgres(None)
