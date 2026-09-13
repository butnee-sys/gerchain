from dee_security.connector_governance import (
    ConnectorAccessRequest,
    ConnectorGovernanceError,
    authorize_connector_access,
)
from dee_security.root_of_trust import RootOfTrust


def _root() -> RootOfTrust:
    return RootOfTrust(owner_id="OWNER-001", owner_public_key="key", genesis_anchor="genesis", policy_version="1")


def _request(actor_id="OWNER-001"):
    return ConnectorAccessRequest("EXIM", "release_escrow_authorized", "REQ-1", actor_id, "NONCE-1")


def _trinity():
    return {"trust": True, "transparency": True, "performance": True}


def test_governed_connector_access_passes():
    authorize_connector_access(root=_root(), request=_request(), trinity_proof=_trinity())


def test_non_owner_connector_is_rejected():
    try:
        authorize_connector_access(root=_root(), request=_request("APP-001"), trinity_proof=_trinity())
    except ConnectorGovernanceError:
        return
    raise AssertionError("non-owner connector access must fail closed")


def test_missing_trinity_is_rejected():
    try:
        authorize_connector_access(root=_root(), request=_request(), trinity_proof={"trust": True})
    except ConnectorGovernanceError:
        return
    raise AssertionError("missing Trinity dimension must fail closed")
