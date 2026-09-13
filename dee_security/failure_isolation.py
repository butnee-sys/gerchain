"""Fail-closed failure isolation between DEE components and the protected core."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .root_of_trust import RootOfTrust, SecurityError
from .trinity import TrinityError, require_trinity


class FailureIsolationError(SecurityError):
    """Raised when a failed component attempts to cross its recovery boundary."""


@dataclass(frozen=True)
class FailureIsolationRequest:
    component_id: str
    incident_id: str
    actor_id: str
    operation: str
    target: str
    recovery_mode: str


def authorize_failure_isolation(
    *,
    root: RootOfTrust,
    request: FailureIsolationRequest,
    trinity_proof: Mapping[str, bool],
) -> None:
    """Permit only governed, fail-closed isolation actions."""
    for name, value in vars(request).items():
        if not str(value).strip():
            raise FailureIsolationError(f"{name} is required")
    if request.actor_id != root.owner_id:
        raise FailureIsolationError("failure isolation actor is not bound to DEE Owner")
    if request.recovery_mode not in {"ISOLATE", "RECOVER"}:
        raise FailureIsolationError("unsupported recovery mode")
    if request.target == "NEF_GERCHAIN" and request.recovery_mode == "ISOLATE":
        # Core isolation is allowed; it must never become an implicit bypass.
        pass
    try:
        require_trinity(trinity_proof)
    except TrinityError as exc:
        raise FailureIsolationError(str(exc)) from exc


__all__ = ["FailureIsolationError", "FailureIsolationRequest", "authorize_failure_isolation"]
