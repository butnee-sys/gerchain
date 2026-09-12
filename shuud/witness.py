"""SHUUD adapter to the existing GerChain WitnessChain.

SHUUD never creates a second witness chain. This adapter only records
application milestones through the existing append_event contract, while
marking every application payload with an explicit SHUUD domain.
"""

from threading import Lock

from witness.chain import WitnessChain

from .domain import canonical_shuud_payload
from .evidence import EvidenceEnvelope
from .shiid import SHIIDDecision
from .release import ReleaseAuthorization

_RELEASE_AUTH_WITNESS_LOCK = Lock()


def _append_shuud_event(
    witness: WitnessChain,
    *,
    event_id: str,
    event_type: str,
    incident_id: str,
    timestamp: str,
    payload: dict,
    evidence: dict,
):
    return witness.append_event(
        event_id=event_id,
        event_type=event_type,
        timestamp=timestamp,
        payload=canonical_shuud_payload(event_type, incident_id, payload),
        evidence=canonical_shuud_payload(event_type, incident_id, evidence),
    )


def record_evidence_locked(witness: WitnessChain, evidence: EvidenceEnvelope, *, timestamp: str):
    return _append_shuud_event(
        witness,
        event_id=f"{evidence.incident_id}-EVIDENCE-LOCKED",
        event_type="SHUUD_EVIDENCE_LOCKED",
        incident_id=evidence.incident_id,
        timestamp=timestamp,
        payload={"content_hash": evidence.content_hash, "evidence_refs": list(evidence.evidence_refs)},
        evidence={"content_hash": evidence.content_hash},
    )


def record_shiid_decision(witness: WitnessChain, decision: SHIIDDecision, *, timestamp: str):
    return _append_shuud_event(
        witness,
        event_id=f"{decision.incident_id}-SHIID",
        event_type="SHIID_DECISION",
        incident_id=decision.incident_id,
        timestamp=timestamp,
        payload={
            "decision": decision.decision.value,
            "rule_version": decision.rule_version,
            "reasons": list(decision.reasons),
            "damage_estimate_nef": decision.damage_estimate_nef,
        },
        evidence={
            "decision": decision.decision.value,
            "rule_version": decision.rule_version,
            "damage_estimate_nef": decision.damage_estimate_nef,
        },
    )


def record_release_authorized(witness: WitnessChain, authorization: ReleaseAuthorization, *, timestamp: str):
    """Record one release authorization event; concurrent replays are idempotent."""
    event_id = f"{authorization.incident_id}-RELEASE-AUTHORIZED"
    with _RELEASE_AUTH_WITNESS_LOCK:
        for entry in witness.entries:
            if getattr(entry.record, "event_id", None) == event_id:
                return entry

        return _append_shuud_event(
            witness,
            event_id=event_id,
            event_type="SHUUD_RELEASE_AUTHORIZED",
            incident_id=authorization.incident_id,
            timestamp=timestamp,
            payload={
                "escrow_id": authorization.escrow_id,
                "rule_version": authorization.rule_version,
                "authorization_hash": authorization.authorization_hash,
            },
            evidence={"authorization_hash": authorization.authorization_hash},
        )


__all__ = ["record_evidence_locked", "record_shiid_decision", "record_release_authorized"]
