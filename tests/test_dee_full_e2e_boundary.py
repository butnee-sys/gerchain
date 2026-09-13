from pathlib import Path


def test_e2e_proof_is_governance_only_and_core_path_remains_indirect():
    root = Path(__file__).resolve().parents[1]
    proof = (root / "dee_security" / "e2e_governance.py").read_text(encoding="utf-8")
    docs = (root / "docs" / "DEE_FULL_E2E_PROOF.md").read_text(encoding="utf-8")
    assert "require_dee_e2e_proof" in proof
    assert "NEF_GERCHAIN" not in proof
    assert "fail-closed" in proof
    assert "Digital Economy → DEE → NEF + GerChain" in docs
    assert "SHUUD/SHIID" in docs
    assert "audit cannot manufacture authorization" in docs
