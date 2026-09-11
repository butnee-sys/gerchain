"""SHUUD adapter to the existing GerChain WitnessChain.

SHUUD never creates a second witness chain. This adapter only records
application milestones through the existing append_event contract.
"""

from typing import Any

from witness.chain import WitnessChain

from .evidence import EvidenceEnvelope
from .shiid import SHIIDDecision
from .release import ReleaseAuthorization


def record_evidence_locked(
    witness: WitnessChain,
    evidence: EvidenceEnvelope,
    *,
    timestamp: str,
):
    return witness.append_event(
        event_id=f"{evidence.incident_id}-EVIDENCE-LOCKED",
        event_type="SHUUD_EVIDENCE_LOCKED",
        timestamp=timestamp,
        payload={
            "incident_id": evidence.incident_id,
            "content_hash": evidence.content_hash,
            "evidence_refs": list(evidence.evidence_refs),
        },
        evidence={
            "incident_id": evidence.incident_id,
            "content_hash": evidence.content_hash,
        },
    )


def record_shiid_decision(
    witness: WitnessChain,
    decision: SHIIDDecision,
    *,
    timestamp: str,
):
    return witness.append_event(
        event_id=f"{decision.incident_id}-SHIID",
        event_type="SHIID_DECISION",
        timestamp=timestamp,
        payload={
            "incident_id": decision.incident_id,
            "decision": decision.decision.value,
            "rule_version": decision.rule_version,
            "reasons": list(decision.reasons),
        },
        evidence={
            "incident_id": decision.incident_id,
            "decision": decision.decision.value,
            "rule_version": decision.rule_version,
        },
    )


def record_release_authorized(
    witness: WitnessChain,
    authorization: ReleaseAuthorization,
    *,
    timestamp: str,
):
    return witness.append_event(
        event_id=f"{authorization.incident_id}-RELEASE-AUTHORIZED",
        event_type="SHUUD_RELEASE_AUTHORIZED",
        timestamp=timestamp,
        payload={
            "incident_id": authorization.incident_id,
            "escrow_id": authorization.escrow_id,
            "rule_version": authorization.rule_version,
            "authorization_hash": authorization.authorization_hash,
        },
        evidence={
            "incident_id": authorization.incident_id,
            "authorization_hash": authorization.authorization_hash,
        },
    )


__all__ = [
    "record_evidence_locked",
    "record_shiid_decision",
    "record_release_authorized",
]
