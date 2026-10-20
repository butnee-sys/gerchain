from __future__ import annotations

from scripts.production_self_repair import diagnose, repair_entrypoint


def _good_entrypoint() -> str:
    return """
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory
factory = ProductionRuntimeFactory(config, engine=engine, session_factory=session_factory)
runtime = factory.create()
"""


def _good_factory() -> str:
    return """
def create(self):
    self.initialize()
    runtime.configure_canonical_ledger(self.session_factory)
    runtime.require_canonical_ledger_authority()
def initialize(self):
    initialize_canonical_postgres_schema(self.engine)
"""


def test_diagnose_accepts_canonical_factory_contract():
    assert diagnose(_good_entrypoint(), _good_factory()) == []


def test_diagnose_reports_all_wiring_drift_at_once():
    issues = diagnose("runtime = ProductionRuntimeFactory.create()", "def create(self): pass")
    assert issues == [
        "ENTRYPOINT_CONFIG_IMPORT_MISSING",
        "ENTRYPOINT_FACTORY_INSTANCE_CONTRACT",
        "FACTORY_CANONICAL_AUTHORITY_DRIFT",
        "FACTORY_MIGRATION_GATE_DRIFT",
        "FACTORY_FAIL_CLOSED_GATE_MISSING",
    ]


def test_repair_rewrites_only_the_approved_legacy_constructor_pattern():
    legacy = """
from services.gerchain_runtime_factory import ProductionRuntimeFactory
runtime = ProductionRuntimeFactory.create(
    escrow_id=escrow_id,
    amount=amount,
    currency=currency,
    witness_id=witness_id,
    engine=engine,
    session_factory=session_factory,
)
"""
    fixed, changed = repair_entrypoint(legacy)
    assert changed
    assert "ProductionRuntimeConfig(" in fixed
    assert "factory = ProductionRuntimeFactory(" in fixed
    assert "runtime = factory.create()" in fixed
    assert "ProductionRuntimeFactory.create(" not in fixed


def test_repair_refuses_unknown_mismatch_without_mutating_source():
    unknown = "runtime = ProductionRuntimeFactory.create(escrow_id=escrow_id)"
    try:
        repair_entrypoint(unknown)
    except RuntimeError as exc:
        assert "no changes written" in str(exc)
    else:
        raise AssertionError("unknown source drift must fail closed")
