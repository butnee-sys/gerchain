from pathlib import Path


def test_failure_isolation_boundary_is_documented():
    root = Path(__file__).resolve().parents[1]
    module = (root / "dee_security" / "failure_isolation.py").read_text(encoding="utf-8")
    doc = (root / "docs" / "DEE_FAILURE_ISOLATION_RECOVERY.md").read_text(encoding="utf-8")
    assert "authorize_failure_isolation" in module
    assert "NEF_GERCHAIN" in module
    assert "Root of Trust" in doc
    assert "Trinity" in doc
    assert "Audit" in doc
    assert "Isolate" in doc
    assert "Governed Recovery" in doc
