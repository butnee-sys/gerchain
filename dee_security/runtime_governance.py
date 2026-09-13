"""DEE runtime governance: explicit roles with fail-closed authorization."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet


class RuntimeGovernanceError(PermissionError):
    """Raised whenever runtime authorization is denied."""


class RuntimeRole(str, Enum):
    OWNER = "OWNER"
    OPERATOR = "OPERATOR"
    APPLICATION = "APPLICATION"


class RuntimeAction(str, Enum):
    ARCHITECTURE = "architecture"
    SECURITY_POLICY = "security_policy"
    ADAPTER_APPROVAL = "adapter_approval"
    RELEASE_APPROVAL = "release_approval"
    MONITORING = "monitoring"
    OPERATIONS = "operations"
    ROUTINE_ACTIONS = "routine_actions"
    CONTRACT_API = "contract_api"


@dataclass(frozen=True)
class RuntimeIdentity:
    identity_id: str
    role: RuntimeRole


@dataclass(frozen=True)
class RuntimeAuthorization:
    identity_id: str
    role: RuntimeRole
    action: RuntimeAction


class RuntimeGovernance:
    """Central deny-by-default runtime role/action policy."""

    _ROLE_ACTIONS: dict[RuntimeRole, FrozenSet[RuntimeAction]] = {
        RuntimeRole.OWNER: frozenset({
            RuntimeAction.ARCHITECTURE,
            RuntimeAction.SECURITY_POLICY,
            RuntimeAction.ADAPTER_APPROVAL,
            RuntimeAction.RELEASE_APPROVAL,
        }),
        RuntimeRole.OPERATOR: frozenset({
            RuntimeAction.MONITORING,
            RuntimeAction.OPERATIONS,
            RuntimeAction.ROUTINE_ACTIONS,
        }),
        RuntimeRole.APPLICATION: frozenset({RuntimeAction.CONTRACT_API}),
    }

    def authorize(
        self,
        identity: RuntimeIdentity,
        action: RuntimeAction,
    ) -> RuntimeAuthorization:
        if not identity.identity_id:
            raise RuntimeGovernanceError("runtime identity is required")
        if not isinstance(identity.role, RuntimeRole):
            raise RuntimeGovernanceError("unknown runtime role")
        if not isinstance(action, RuntimeAction):
            raise RuntimeGovernanceError("unknown runtime action")
        if action not in self._ROLE_ACTIONS.get(identity.role, frozenset()):
            raise RuntimeGovernanceError(
                f"role {identity.role.value} is not authorized for {action.value}"
            )
        return RuntimeAuthorization(
            identity_id=identity.identity_id,
            role=identity.role,
            action=action,
        )

    def is_allowed(self, identity: RuntimeIdentity, action: RuntimeAction) -> bool:
        try:
            self.authorize(identity, action)
        except RuntimeGovernanceError:
            return False
        return True


__all__ = [
    "RuntimeAction",
    "RuntimeAuthorization",
    "RuntimeGovernance",
    "RuntimeGovernanceError",
    "RuntimeIdentity",
    "RuntimeRole",
]
