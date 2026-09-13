import pytest

from connectors import EXIMConnectorAdapter
from gateway.open_multi_connector import OpenMultiConnectorGateway


class Adapter:
    connector_id = "EXIM"

    def ping(self, **kwargs):
        return kwargs.get("value", "ok")


def test_authenticated_dispatch_requires_credential_and_nonce():
    gateway = OpenMultiConnectorGateway()
    gateway.register(Adapter(), credential="secret", allowed_operations={"ping"})
    assert gateway.dispatch("EXIM", "ping", credential="secret", nonce="n-1", value="ok") == "ok"


def test_registration_without_credential_is_denied():
    gateway = OpenMultiConnectorGateway()
    with pytest.raises(TypeError):
        gateway.register(EXIMConnectorAdapter())
    assert gateway.registered_connectors() == ()


def test_dispatch_without_credential_is_denied():
    gateway = OpenMultiConnectorGateway()
    gateway.register(Adapter(), credential="secret", allowed_operations={"ping"})
    with pytest.raises(ValueError, match="credential"):
        gateway.dispatch("EXIM", "ping", nonce="n-2")


def test_replay_is_denied():
    gateway = OpenMultiConnectorGateway()
    gateway.register(Adapter(), credential="secret", allowed_operations={"ping"})
    gateway.dispatch("EXIM", "ping", credential="secret", nonce="n-1")
    try:
        gateway.dispatch("EXIM", "ping", credential="secret", nonce="n-1")
    except ValueError as exc:
        assert "already used" in str(exc)
        return
    raise AssertionError("replayed nonce must be denied")


def test_revoked_connector_is_denied():
    gateway = OpenMultiConnectorGateway()
    gateway.register(Adapter(), credential="secret", allowed_operations={"ping"})
    gateway.revoke("EXIM")
    try:
        gateway.dispatch("EXIM", "ping", credential="secret", nonce="n-1")
    except ValueError as exc:
        assert "revoked" in str(exc)
        return
    raise AssertionError("revoked connector must be denied")
