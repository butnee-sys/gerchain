import pytest

from application_adapters import SHUUDApplicationAdapter
from connectors import EXIMConnectorAdapter
from gateway import OpenMultiConnectorGateway


def build_gateway(credential: str = "SHUUD-SECRET") -> OpenMultiConnectorGateway:
    gateway = OpenMultiConnectorGateway()
    gateway.register(
        EXIMConnectorAdapter(),
        credential=credential,
        allowed_operations={
            "export_status",
            "export_escrow_status",
            "export_settlement_status",
            "export_evidence_status",
            "export_audit_event",
            "create_witness_chain",
            "restore_witness_chain",
            "create_escrow",
            "restore_escrow",
            "verifier",
            "release_escrow",
            "release_escrow_authorized",
        },
    )
    return gateway


def test_shuud_application_adapter_requires_credential():
    gateway = OpenMultiConnectorGateway()
    with pytest.raises(ValueError, match="credential is required"):
        SHUUDApplicationAdapter(gateway=gateway, credential="")
    assert gateway.registered_connectors() == ()


def test_shuud_application_adapter_requires_composition_boundary_registration():
    gateway = OpenMultiConnectorGateway()
    with pytest.raises(ValueError, match="connector must be registered at the composition boundary"):
        SHUUDApplicationAdapter(gateway=gateway, credential="SHUUD-SECRET")


def test_shuud_application_adapter_uses_authenticated_registered_connector():
    gateway = build_gateway()
    adapter = SHUUDApplicationAdapter(gateway=gateway, credential="SHUUD-SECRET")

    assert adapter.connector_id == "EXIM"
    assert gateway.registered_connectors() == ("EXIM",)


def test_shuud_application_adapter_generates_fresh_nonce_for_each_dispatch(monkeypatch):
    gateway = build_gateway()
    adapter = SHUUDApplicationAdapter(gateway=gateway, credential="SHUUD-SECRET")
    captured = []
    original_dispatch = gateway.dispatch

    def capture_dispatch(connector_id, operation, *, credential, nonce, **kwargs):
        captured.append((connector_id, operation, credential, nonce))
        return original_dispatch(
            connector_id,
            operation,
            credential=credential,
            nonce=nonce,
            **kwargs,
        )

    monkeypatch.setattr(gateway, "dispatch", capture_dispatch)

    adapter.export_status(status="ACTIVE", reference_id="CASE-1")
    adapter.export_status(status="ACTIVE", reference_id="CASE-2")

    assert len(captured) == 2
    assert captured[0][0:3] == ("EXIM", "export_status", "SHUUD-SECRET")
    assert captured[1][0:3] == ("EXIM", "export_status", "SHUUD-SECRET")
    assert captured[0][3].startswith("SHUUD-")
    assert captured[1][3].startswith("SHUUD-")
    assert captured[0][3] != captured[1][3]


def test_shuud_application_adapter_wrong_credential_is_denied():
    gateway = build_gateway()
    adapter = SHUUDApplicationAdapter(gateway=gateway, credential="SHUUD-SECRET")
    adapter.credential = "WRONG-SECRET"

    with pytest.raises(ValueError, match="authentication failed"):
        adapter.export_status(status="ACTIVE", reference_id="CASE-3")


def test_shuud_application_adapter_does_not_rebind_existing_connector_with_new_credential():
    gateway = build_gateway("SHUUD-FIRST")
    first = SHUUDApplicationAdapter(gateway=gateway, credential="SHUUD-FIRST")
    second = SHUUDApplicationAdapter(gateway=gateway, credential="SHUUD-SECOND")

    assert first.credential == "SHUUD-FIRST"
    assert second.credential == "SHUUD-SECOND"
    with pytest.raises(ValueError, match="authentication failed"):
        second.export_status(status="ACTIVE", reference_id="CASE-4")
    assert first.export_status(status="ACTIVE", reference_id="CASE-5").reference_id == "CASE-5"
