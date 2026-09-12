"""SHUUD -> GerChain release authorization bridge.

This module does not implement a second escrow engine. It creates an
immutable release authorization from a SHIID approval and delegates the
actual state transition to the existing GerChain EscrowEngine.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from core.hashing import domain_hash
from escrow.engine import EscrowEngine

from .shiid import Decision, SHIIDDecision


@dataclass(frozen=True)
class ReleaseAuthorization:
    incident_id: str
    escrow_id: str
    rule_version: str
    authorization_hash: str
    damage_estimate_nef: float | None = None


_RELEASE_LOCK = Lock()


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
    if decision.damage_estimate_nef is None:
        raise ValueError("damage_estimate_nef is required")
    if isinstance(decision.damage_estimate_nef, bool):
        raise ValueError("damage_estimate_nef must be numeric")

    payload = {
        "incident_id": decision.incident_id,
        "escrow_id": escrow_id.strip(),
        "rule_version": decision.rule_version,
        "decision": decision.decision.value,
        "reasons": list(decision.reasons),
        "damage_estimate_nef": decision.damage_estimate_nef,
    }

    return ReleaseAuthorization(
        incident_id=decision.incident_id,
        escrow_id=escrow_id.strip(),
        rule_version=decision.rule_version,
        authorization_hash=domain_hash("SHUUD_RELEASE_AUTH", payload),
        damage_estimate_nef=decision.damage_estimate_nef,
    )


def release_escrow(
    escrow: EscrowEngine,
    authorization: ReleaseAuthorization,
    *,
    timestamp: str | None = None,
    evidence: Any | None = None,
):
    """Delegate LOCKED -> RELEASED atomically within this sandbox process."""
    with _RELEASE_LOCK:
        if escrow.escrow_id != authorization.escrow_id:
            raise ValueError("authorization does not belong to escrow")

        if authorization.damage_estimate_nef is None:
            raise ValueError("authorization amount is missing")
        if escrow.amount != authorization.damage_estimate_nef:
            raise ValueError("authorization amount does not belong to escrow")

        state = escrow.get_state()
        if state["state"] != "LOCKED":
            raise ValueError(
                f"SHUUD release requires LOCKED escrow, got {state['state']}"
            )

        release_timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        release_evidence = evidence or {
            "incident_id": authorization.incident_id,
            "authorization_hash": authorization.authorization_hash,
            "rule_version": authorization.rule_version,
            "damage_estimate_nef": authorization.damage_estimate_nef,
        }

        return escrow.transition(
            "RELEASED",
            release_timestamp,
            release_evidence,
        )


__all__ = [
    "ReleaseAuthorization",
    "authorize_release",
    "release_escrow",
]
