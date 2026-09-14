"""SHUUD release authorization through the application adapter boundary."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from application_adapters import SHUUDApplicationAdapter

from .shiid import Decision, SHIIDDecision


@dataclass(frozen=True)
class ReleaseAuthorization:
    incident_id: str
    escrow_id: str
    rule_version: str
    authorization_hash: str


def _authorization_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def authorize_release(decision: SHIIDDecision, *, escrow_id: str) -> ReleaseAuthorization:
    """Create a release authorization only from an APPROVE decision."""
    if decision.decision is not Decision.APPROVE:
        raise ValueError("SHIID decision is not APPROVE")
    if not escrow_id or not escrow_id.strip():
        raise ValueError("escrow_id is required")

    payload = {"incident_id": decision.incident_id, "escrow_id": escrow_id.strip(), "rule_version": decision.rule_version, "decision": decision.decision.value, "reasons": list(decision.reasons)}
    return ReleaseAuthorization(incident_id=decision.incident_id, escrow_id=escrow_id.strip(), rule_version=decision.rule_version, authorization_hash=_authorization_hash(payload))


def release_escrow(escrow: Any, authorization: ReleaseAuthorization, *, app_adapter: SHUUDApplicationAdapter, timestamp: str | None = None, evidence: Any | None = None):
    """Delegate LOCKED -> RELEASED through the already-composed application boundary."""
    return app_adapter.release_escrow(escrow, authorization_hash=authorization.authorization_hash, incident_id=authorization.incident_id, rule_version=authorization.rule_version, timestamp=timestamp or datetime.now(timezone.utc).isoformat(), evidence=evidence)


__all__ = ["ReleaseAuthorization", "authorize_release", "release_escrow"]
