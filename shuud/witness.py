"""SHUUD application events recorded through the EXIM Escrow Port."""

from typing import Any

from nef_gerchain_port import ExternalPortImport
from .domain import canonical_shuud_payload
from .evidence import EvidenceEnvelope
from .shiid import SHIIDDecision
from .release import ReleaseAuthorization


_PORT_IMPORT = ExternalPortImport()


def _append_shuud_event(
    witness: Any,
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


def record_evidence_locked(witness: Any, evidence: EvidenceEnvelope, *, timestamp: str):
    return _append_shuud_event(
        witness,
        event_id=f"{evidence.incident_id}-EVIDENCE-LOCKED",
        event_type="SHUUD_EVIDENCE_LOCKED",
        incident_id=evidence.incident_id,
        timestamp=timestamp,
        payload={"content_hash": evidence.content_hash, "evidence_refs": list(evidence.evidence_refs)},
        evidence={"content_hash": evidence.content_hash},
    )


def record_shiid_decision(witness: Any, decision: SHIIDDecision, *, timestamp: str):
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
            "damage_estimate_mnt": decision.damage_estimate_mnt,
        },
        evidence={
            "decision": decision.decision.value,
            "rule_version": decision.rule_version,
            "damage_estimate_mnt": decision.damage_estimate_mnt,
        },
    )


def record_release_authorized(witness: Any, authorization: ReleaseAuthorization, *, timestamp: str):
    return _append_shuud_event(
        witness,
        event_id=f"{authorization.incident_id}-RELEASE-AUTHORIZED",
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
