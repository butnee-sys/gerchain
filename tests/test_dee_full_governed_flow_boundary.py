from pathlib import Path


def test_full_e2e_proof_is_not_an_authority_bypass():
    source = Path("dee_security/e2e_governance.py").read_text(encoding="utf-8")
    assert "NEF_GERCHAIN" not in source
    assert "import nef_gerchain_port" not in source
    assert "import escrow" not in source
    assert "require_trinity" in source
    assert "proof.require_complete()" in source


def test_full_e2e_scenario_keeps_business_app_outside_core():
    source = Path("tests/test_dee_full_governed_flow_e2e.py").read_text(encoding="utf-8")
    assert "application_adapters" not in source
    assert "shuud" not in source.lower()
    assert "EXIMConnectorAdapter" in source
