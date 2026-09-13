import pytest

from connectors import EXIMConnectorAdapter
from gateway import OpenMultiConnectorGateway


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
