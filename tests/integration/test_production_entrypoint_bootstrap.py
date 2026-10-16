import os

from production_entrypoint import build_production_runtime


def test_production_entrypoint_bootstraps_canonical_runtime(monkeypatch):
    monkeypatch.setenv("GERCHAIN_ESCROW_ID", os.environ.get("GERCHAIN_ESCROW_ID", "entrypoint-test-escrow"))
    monkeypatch.setenv("GERCHAIN_ESCROW_AMOUNT", os.environ.get("GERCHAIN_ESCROW_AMOUNT", "100"))
    monkeypatch.setenv("GERCHAIN_CURRENCY", os.environ.get("GERCHAIN_CURRENCY", "MNT"))
    monkeypatch.setenv("GERCHAIN_WITNESS_ID", os.environ.get("GERCHAIN_WITNESS_ID", "entrypoint-test-witness"))
    runtime, engine = build_production_runtime()
    try:
        assert runtime.is_canonical_ledger_authoritative
        assert runtime.runtime_mode == "production-postgresql"
        assert runtime.escrow_engine.escrow_id == os.environ["GERCHAIN_ESCROW_ID"]
    finally:
        engine.dispose()
