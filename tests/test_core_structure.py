from pathlib import Path


def test_core_structure_manifest_is_present():
    root = Path(__file__).resolve().parents[1]
    required = (
        "architecture/contracts.py",
        "architecture/ports.py",
        "architecture/governed_flow_adapters.py",
        "architecture/composition_root.py",
        "dee/self_maintainer.py",
        "services/g3_core_handler.py",
        "services/g3_dee_authorized_handler.py",
        "services/exim_gateway.py",
        "services/i2b_service_center.py",
        "services/i2b_services.py",
        "persistence/atomic_release.py",
        "persistence/governed_atomic_release.py",
        "persistence/idempotency_store.py",
        "persistence/recovery_outbox.py",
        "docs/ARCHITECTURE_FREEZE.md",
        "docs/CORE_BASELINE.md",
    )
    missing = [path for path in required if not (root / path).is_file()]
    assert not missing, f"core structure missing: {missing}"


def test_shuud_is_not_part_of_core_acceptance_manifest():
    root = Path(__file__).resolve().parents[1]
    baseline = (root / "docs/CORE_BASELINE.md").read_text(encoding="utf-8")
    assert "SHUUD tests are intentionally outside this core acceptance gate." in baseline


def test_core_boundary_rule_is_explicit():
    root = Path(__file__).resolve().parents[1]
    baseline = (root / "docs/CORE_BASELINE.md").read_text(encoding="utf-8")
    assert "Layer" in baseline
    assert "EXIM is a boundary, not a value-flow engine." in baseline
    assert "NEF owns asset truth; GerChain owns value flow." in baseline
