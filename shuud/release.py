"""SHUUD -> EXIM Escrow Port release authorization bridge.

SHUUD creates the release authorization from a SHIID approval. The actual
GerChain escrow state transition is delegated to the external Port so SHUUD
does not import or call GerChain core engines directly.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from nef_gerchain_port import ExternalPortImport

from .shiid import Decision, SHIIDDecision


@dataclass(frozen=True)
class ReleaseAuthorization:
    incident_id: str
    escrow_id: str
    rule_version: str
    authorization_hash: str


def authorize_release(
    decision: SHIIDDecision,
    *,
    escrow_id: str,
) -> ReleaseAuthorization:
    """Create a release authorization only from an APPROVE decision."""
    if decision.decision is not Decision.APPROVE:
        raise ValueError("SHIID decision is not APPROVE")
    if not escrow_id or not escrow_id.strip():
        raise ValueError("escrow_id is required")

    payload = {
        "incident_id": decision.incident_id,
        "escrow_id": escrow_id.strip(),
        "rule_version": decision.rule_version,
        "decision": decision.decision.value,
        "reasons": list(decision.reasons),
    }

    # Keep the SHUUD authorization hash local to the application boundary.
    import hashlib
    import json

    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    authorization_hash = hashlib.sha256(
        ("SHUUD_RELEASE_AUTH:" + canonical).encode("utf-8")
    ).hexdigest()

    return ReleaseAuthorization(
        incident_id=decision.incident_id,
        escrow_id=escrow_id.strip(),
        rule_version=decision.rule_version,
        authorization_hash=authorization_hash,
    )


def release_escrow(
    escrow: Any,
    authorization: ReleaseAuthorization,
    *,
    timestamp: str | None = None,
    evidence: Any | None = None,
):
    """Delegate LOCKED -> RELEASED to the EXIM Escrow Port."""
    port = ExternalPortImport()
    release_timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    return port.release_escrow(
        escrow,
        incident_id=authorization.incident_id,
        authorization_hash=authorization.authorization_hash,
        rule_version=authorization.rule_version,
        timestamp=release_timestamp,
        evidence=evidence,
    )


__all__ = [
    "ReleaseAuthorization",
    "authorize_release",
    "release_escrow",
]
