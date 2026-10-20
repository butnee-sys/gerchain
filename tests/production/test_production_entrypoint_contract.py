from __future__ import annotations

from pathlib import Path


def test_production_entrypoint_uses_runtime_factory_instance_contract():
    source = Path("production_entrypoint.py").read_text(encoding="utf-8")
    assert "ProductionRuntimeConfig(" in source
    assert "ProductionRuntimeFactory(" in source
    assert "factory.create()" in source
    assert "ProductionRuntimeFactory.create(" not in source


def test_production_entrypoint_requires_canonical_ledger_authority():
    source = Path("production_entrypoint.py").read_text(encoding="utf-8")
    assert "runtime.is_canonical_ledger_authoritative" in source
    assert "canonical ledger authority was not established" in source
