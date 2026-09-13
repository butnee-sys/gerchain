import pytest

from connectors import EXIMConnectorAdapter
from gateway import OpenMultiConnectorGateway


READ_OPS = {"export_status"}


def authenticated_gateway():
    gateway = OpenMultiConnectorGateway()
    gateway.register(EXIMConnectorAdapter(), credential="EXIM-SANDBOX-SECRET", allowed_operations=READ_OPS)
    return gateway


def test_gateway_registers_and_dispatches_named_connector():
    gateway = OpenMultiConnectorGateway()
    adapter = EXIMConnectorAdapter()
    gateway.register(adapter)
    assert gateway.registered_connectors() == ("EXIM",)
    result = gateway.dispatch("EXIM", "export_status", status="ACTIVE", reference_id="CASE-1")
    assert result.status == "ACTIVE"
    assert result.reference_id == "CASE-1"


def test_gateway_rejects_unknown_connector():
    gateway = OpenMultiConnectorGateway()
    with pytest.raises(ValueError, match="not registered"):
        gateway.connector("UNKNOWN")


def test_gateway_rejects_duplicate_connector():
    gateway = OpenMultiConnectorGateway()
    gateway.register(EXIMConnectorAdapter())
    with pytest.raises(ValueError, match="already registered"):
        gateway.register(EXIMConnectorAdapter())


def test_gateway_revocation_removes_connector():
    gateway = OpenMultiConnectorGateway()
    gateway.register(EXIMConnectorAdapter())
    gateway.revoke("EXIM")
    assert gateway.registered_connectors() == ()


def test_authenticated_gateway_accepts_valid_identity_and_operation():
    gateway = authenticated_gateway()
    result = gateway.dispatch(
        "EXIM", "export_status", credential="EXIM-SANDBOX-SECRET", nonce="N-001",
        status="ACTIVE", reference_id="CASE-2",
    )
    assert result.reference_id == "CASE-2"


def test_authenticated_gateway_rejects_bad_credential():
    gateway = authenticated_gateway()
    with pytest.raises(ValueError, match="authentication failed"):
        gateway.dispatch(
            "EXIM", "export_status", credential="WRONG", nonce="N-002",
            status="ACTIVE", reference_id="CASE-3",
        )


def test_authenticated_gateway_rejects_unauthorized_operation():
    gateway = authenticated_gateway()
    with pytest.raises(ValueError, match="not authorized"):
        gateway.dispatch(
            "EXIM", "release_escrow", credential="EXIM-SANDBOX-SECRET", nonce="N-003",
        )


def test_authenticated_gateway_rejects_replayed_nonce():
    gateway = authenticated_gateway()
    kwargs = dict(
        credential="EXIM-SANDBOX-SECRET", nonce="N-004",
        status="ACTIVE", reference_id="CASE-4",
    )
    gateway.dispatch("EXIM", "export_status", **kwargs)
    with pytest.raises(ValueError, match="already used"):
        gateway.dispatch("EXIM", "export_status", **kwargs)


def test_authenticated_gateway_rejects_revoked_connector():
    gateway = authenticated_gateway()
    gateway.revoke("EXIM")
    with pytest.raises(ValueError, match="not registered"):
        gateway.dispatch(
            "EXIM", "export_status", credential="EXIM-SANDBOX-SECRET", nonce="N-005",
            status="ACTIVE", reference_id="CASE-5",
        )
