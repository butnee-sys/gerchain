"""DEE EXIM Port security boundary.

The EXIM Port is the controlled boundary between the protected NEF–GerChain
core and external connector/application layers. It never becomes a source of
core authority; it verifies an already-governed request and fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .core_access import CoreAccessRequest, authorize_core_access
from .evidence_governance import ProtectedEvidence, require_protected_evidence
from .root_of_trust import RootOfTrust, SecurityError
from .trinity import require_trinity


class EXIMPortSecurityError(SecurityError):
    """Raised when an EXIM boundary request violates DEE protection."""


@dataclass(frozen=True)
class EXIMPortRequest:
    request_id: str
    actor_id: str
    operation: str
    contract_id: str
    evidence: ProtectedEvidence


def authorize_exim_port_request(
    *,
    root: RootOfTrust,
    request: EXIMPortRequest,
    evidence_payload: Any,
    trinity_proof: Mapping[str, bool],
) -> None:
    """Authorize an EXIM request only through the governed core path."""
    if not request.request_id or not request.contract_id:
        raise EXIMPortSecurityError("request_id and contract_id are required")
    require_trinity(trinity_proof)
    try:
        authorize_core_access(
            root=root,
            request=CoreAccessRequest(
                actor_id=request.actor_id,
                operation=request.operation,
                entrypoint="CORE_ADAPTER",
                request_id=request.request_id,
            ),
            trinity_proof=trinity_proof,
            authorized_actor_id=root.owner_id,
        )
        require_protected_evidence(
            root=root,
            evidence=request.evidence,
            payload=evidence_payload,
            trinity_proof=trinity_proof,
        )
    except SecurityError as exc:
        raise EXIMPortSecurityError(str(exc)) from exc


__all__ = ["EXIMPortSecurityError", "EXIMPortRequest", "authorize_exim_port_request"]
