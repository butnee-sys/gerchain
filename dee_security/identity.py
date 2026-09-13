"""DEE identity-to-authorization boundary.

Runtime identity is never treated as sufficient by itself. A protected
operation must have a valid runtime role/action authorization, and the Owner
role must correspond to the DEE Root of Trust owner identity.
"""
from __future__ import annotations

from dataclasses import dataclass

from .root_of_trust import RootOfTrust, SecurityError
from .runtime_governance import (
    RuntimeAction,
    RuntimeAuthorization,
    RuntimeGovernance,
    RuntimeIdentity,
    RuntimeRole,
)


@dataclass(frozen=True)
class ProtectedIdentity:
    """Identity presented at a DEE protected boundary."""

    identity_id: str
    role: RuntimeRole

    def runtime_identity(self) -> RuntimeIdentity:
        return RuntimeIdentity(identity_id=self.identity_id, role=self.role)


def authorize_protected_operation(
    *,
    root: RootOfTrust,
    identity: ProtectedIdentity,
    action: RuntimeAction,
    governance: RuntimeGovernance | None = None,
) -> RuntimeAuthorization:
    """Authorize a runtime operation under the DEE Root of Trust.

    Owner operations are cryptographically bound to ``root.owner_id``.
    All roles remain subject to the central deny-by-default runtime policy.
    """
    if not identity.identity_id:
        raise SecurityError("DEE identity is required")
    if identity.role == RuntimeRole.OWNER and identity.identity_id != root.owner_id:
        raise SecurityError("Owner identity does not match the DEE Root of Trust")

    policy = governance or RuntimeGovernance()
    return policy.authorize(identity.runtime_identity(), action)


__all__ = [
    "ProtectedIdentity",
    "authorize_protected_operation",
]
