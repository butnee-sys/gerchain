import pytest

from composition.shuud import build_shuud_application_adapter


def test_shuud_composition_builds_governed_gateway_from_environment(monkeypatch):
    monkeypatch.setenv("SHUUD_EXIM_CREDENTIAL", "COMPOSITION-SECRET")
    adapter = build_shuud_application_adapter()
    assert adapter.connector_id == "EXIM"
    assert adapter.gateway.registered_connectors() == ("EXIM",)


def test_shuud_composition_requires_credential(monkeypatch):
    monkeypatch.delenv("SHUUD_EXIM_CREDENTIAL", raising=False)
    with pytest.raises(RuntimeError, match="SHUUD_EXIM_CREDENTIAL is required"):
        build_shuud_application_adapter()
