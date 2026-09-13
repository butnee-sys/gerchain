"""Cross-cutting DEE release governance: Root of Trust + Trinity + audit context."""
from __future__ import annotations

import hashlib
import json
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
    witness_state_root: str = ""
    settlement_hash: str = ""
    recovery_decision_hash: str = ""
    execution_chain_hash: str = ""

    def execution_context(self) -> dict[str, str]:
        return {
            "release_id": self.release_id,
            "witness_state_root": self.witness_state_root,
            "settlement_hash": self.settlement_hash,
            "recovery_decision_hash": self.recovery_decision_hash,
        }

    def computed_execution_chain_hash(self) -> str:
        payload = json.dumps(self.execution_context(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def authorize_governed_release(*, root: RootOfTrust, request: ReleaseGovernanceRequest, release_gate: ReleaseAuthorization, policy: Any, release: Any, manifest: Mapping[str, Any], trinity_proof: Mapping[str, bool]) -> None:
    """Apply DEE's outer release gate before the existing signed-release gate."""
    for name, value in vars(request).items():
        if name == "execution_chain_hash":
            continue
        if not str(value).strip() and name in {"release_id", "actor_id", "request_id", "operation"}:
            raise ReleaseGovernanceError(f"{name} is required")
    if request.actor_id != root.owner_id:
        raise ReleaseGovernanceError("release actor is not bound to DEE Owner")
    if request.release_id != release.release_id:
        raise ReleaseGovernanceError("release request/id mismatch")
    try:
        require_trinity(trinity_proof)
    except TrinityError as exc:
        raise ReleaseGovernanceError(str(exc)) from exc

    context_fields = (request.witness_state_root, request.settlement_hash, request.recovery_decision_hash)
    if any(context_fields):
        if not all(str(value).strip() for value in context_fields):
            raise ReleaseGovernanceError("release execution context is incomplete")
        if request.execution_chain_hash != request.computed_execution_chain_hash():
            raise ReleaseGovernanceError("release execution chain binding mismatch")

    try:
        release_gate.authorize(root=root, policy=policy, release=release, manifest=manifest)
    except SecurityError as exc:
        raise ReleaseGovernanceError(str(exc)) from exc


__all__ = ["ReleaseGovernanceError", "ReleaseGovernanceRequest", "authorize_governed_release"]
