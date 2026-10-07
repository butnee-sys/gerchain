import os

from production_entrypoint import build_production_runtime


def test_production_entrypoint_bootstraps_canonical_runtime():
    runtime, engine = build_production_runtime()
    try:
        assert runtime.is_canonical_ledger_authoritative
        assert runtime.runtime_mode == "production-postgresql"
        assert runtime.escrow_engine.escrow_id == os.environ["GERCHAIN_ESCROW_ID"]
    finally:
        engine.dispose()
