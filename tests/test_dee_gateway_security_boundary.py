from pathlib import Path


def test_gateway_security_boundary_is_explicit():
    root = Path(__file__).resolve().parents[1]
    gateway = (root / "gateway" / "open_multi_connector.py").read_text(encoding="utf-8")
    security = (root / "dee_security" / "gateway_governance.py").read_text(encoding="utf-8")
    doc = (root / "docs" / "DEE_GATEWAY_SECURITY.md").read_text(encoding="utf-8")

    assert "nef_gerchain_port" not in gateway
    assert "nef_engine" not in gateway
    assert "gerchain_adapter" not in gateway
    assert "authorize_gateway_access" in security
    assert "Gateway Governance" in doc
    assert "Connector Governance" in doc
    assert "EXIM Port" in doc
    assert "Trinity" in doc
