"""Executable guards for the frozen DEE dependency direction."""

from pathlib import Path


def test_shuud_application_adapter_does_not_import_exim_connector_directly():
    source = Path("application_adapters/shuud.py").read_text(encoding="utf-8")
    assert "from connectors import EXIMConnectorAdapter" not in source
    assert "EXIMConnectorAdapter()" not in source


def test_exim_connector_is_the_port_import_boundary():
    source = Path("connectors/exim_adapter.py").read_text(encoding="utf-8")
    assert "from nef_gerchain_port import" in source


def test_architecture_freeze_exists():
    freeze = Path("docs/DEE_ARCHITECTURE_FREEZE.md")
    assert freeze.exists()
    content = freeze.read_text(encoding="utf-8")
    assert "G3 ESCROW FOUNDATION" in content
    assert "EXIM PORT" in content
    assert "DE–COUNTRY PORT" in content
    assert "I2B MULTI-CONNECTOR GATEWAY" in content
    assert "TRINITY" in content
