import pytest

from dee_security.connector_isolation import (
    ConnectorIsolationError,
    ConnectorIsolationRequest,
    authorize_connector_isolation,
)
from dee_security.root_of_trust import RootOfTrust


def root():
    return RootOfTrust(owner_id="OWNER-001", owner_public_key="key", genesis_anchor="genesis", policy_version="1")


def proof():
    return {"trust": True, "transparency": True, "performance": True}


def request(target="CONNECTOR-A", actor="OWNER-001"):
    return ConnectorIsolationRequest("CONNECTOR-A", "REQ-1", actor, "N-1", target)


def test_same_connector_context_is_allowed():
    authorize_connector_isolation(root=root(), request=request(), trinity_proof=proof())


def test_cross_connector_context_is_denied():
    with pytest.raises(ConnectorIsolationError):
        authorize_connector_isolation(root=root(), request=request("CONNECTOR-B"), trinity_proof=proof())


def test_non_owner_connector_actor_is_denied():
    with pytest.raises(ConnectorIsolationError):
        authorize_connector_isolation(root=root(), request=request(actor="APP-1"), trinity_proof=proof())


def test_missing_trinity_is_denied():
    with pytest.raises(ConnectorIsolationError):
        authorize_connector_isolation(root=root(), request=request(), trinity_proof={"trust": True})
