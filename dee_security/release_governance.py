"""Cross-cutting DEE release governance: Root of Trust + Trinity + audit context."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .release_policy import ReleaseAuthorization
from .root_of_trust import RootOfTrust, SecurityError
from .trinity import TrinityError, require_trinity


class ReleaseGovernanceError(SecurityError):
    """Raised when a release cannot pass the DEE governance boundary."""


@dataclass(frozen=True)
class ReleaseGovernanceRequest:
    release_id: str
    actor_id: str
    request_id: str
    operation: str = "RELEASE"


def authorize_governed_release(
    *,
    root: RootOfTrust,
    request: ReleaseGovernanceRequest,
    release_gate: ReleaseAuthorization,
    policy: Any,
    release: Any,
    manifest: Mapping[str, Any],
    trinity_proof: Mapping[str, bool],
) -> None:
    """Apply DEE's outer release gate before the existing signed-release gate."""
    for name, value in vars(request).items():
        if not str(value).strip():
            raise ReleaseGovernanceError(f"{name} is required")
    if request.actor_id != root.owner_id:
        raise ReleaseGovernanceError("release actor is not bound to DEE Owner")
    if request.release_id != release.release_id:
        raise ReleaseGovernanceError("release request/id mismatch")
    try:
        require_trinity(trinity_proof)
    except TrinityError as exc:
        raise ReleaseGovernanceError(str(exc)) from exc

    try:
        release_gate.authorize(
            root=root,
            policy=policy,
            release=release,
            manifest=manifest,
        )
    except SecurityError as exc:
        raise ReleaseGovernanceError(str(exc)) from exc


__all__ = ["ReleaseGovernanceError", "ReleaseGovernanceRequest", "authorize_governed_release"]
