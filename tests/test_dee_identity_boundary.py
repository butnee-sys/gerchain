"""DEE identity and Root-of-Trust authorization invariants."""

import pytest

from dee_security import ProtectedIdentity, authorize_protected_operation
from dee_security.root_of_trust import RootOfTrust, SecurityError
from dee_security.runtime_governance import RuntimeAction, RuntimeRole


def _root(owner_id: str = "owner-1") -> RootOfTrust:
    # RFC 8032 test-vector public key; only public material is needed here.
    return RootOfTrust(
        owner_id=owner_id,
        public_key_b64="11qYAYLef9nJ7l6J6bV9N9M5f4v4r0VQ3zYQ9q4x0rE=",
    )


def test_owner_identity_must_match_root_of_trust():
    with pytest.raises(SecurityError, match="does not match"):
        authorize_protected_operation(
            root=_root("owner-1"),
            identity=ProtectedIdentity("attacker", RuntimeRole.OWNER),
            action=RuntimeAction.ARCHITECTURE,
        )


def test_owner_can_authorize_owner_action():
    authorization = authorize_protected_operation(
        root=_root(),
        identity=ProtectedIdentity("owner-1", RuntimeRole.OWNER),
        action=RuntimeAction.ARCHITECTURE,
    )
    assert authorization.identity_id == "owner-1"
    assert authorization.role is RuntimeRole.OWNER
    assert authorization.action is RuntimeAction.ARCHITECTURE


def test_application_cannot_authorize_owner_action():
    with pytest.raises(Exception):
        authorize_protected_operation(
            root=_root(),
            identity=ProtectedIdentity("app-1", RuntimeRole.APPLICATION),
            action=RuntimeAction.RELEASE_APPROVAL,
        )


def test_empty_identity_is_denied():
    with pytest.raises(SecurityError, match="identity is required"):
        authorize_protected_operation(
            root=_root(),
            identity=ProtectedIdentity("", RuntimeRole.APPLICATION),
            action=RuntimeAction.CONTRACT_API,
        )
