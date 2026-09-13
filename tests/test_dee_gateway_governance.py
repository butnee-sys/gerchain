from dee_security.gateway_governance import (
    GatewayAccessRequest,
    GatewayGovernanceError,
    authorize_gateway_access,
)
from dee_security.root_of_trust import RootOfTrust


def _root():
    return RootOfTrust(owner_id="OWNER-001", owner_public_key="key", genesis_anchor="genesis", policy_version="1")


def _request(actor_id="OWNER-001"):
    return GatewayAccessRequest("I2B-GW", "EXIM", "release_escrow_authorized", "REQ-GW-1", actor_id, "NONCE-GW-1")


def _trinity():
    return {"trust": True, "transparency": True, "performance": True}


def test_gateway_governance_passes_for_governed_owner_request():
    authorize_gateway_access(root=_root(), request=_request(), trinity_proof=_trinity())


def test_gateway_cannot_grant_non_owner_authority():
    try:
        authorize_gateway_access(root=_root(), request=_request("APP-001"), trinity_proof=_trinity())
    except GatewayGovernanceError:
        return
    raise AssertionError("gateway must not grant independent authority")


def test_gateway_fails_closed_without_trinity():
    try:
        authorize_gateway_access(root=_root(), request=_request(), trinity_proof={"trust": True})
    except GatewayGovernanceError:
        return
    raise AssertionError("gateway must fail closed without complete Trinity")
