"""SHUUD-specific verification boundary.

This module does not implement cryptography or a second witness chain. It
reuses GerChain's existing IndependentVerifier for cryptographic/state
verification and adds only SHUUD domain invariants required before release.
"""

from dataclasses import dataclass
from typing import Any, Dict, Iterable

from verifier.independent_verifier import IndependentVerifier


@dataclass(frozen=True)
class SHUUDVerificationResult:
    verified: bool
    reasons: tuple[str, ...]
    incident_id: str | None = None
    escrow_id: str | None = None


class SHUUDIndependentVerifier:
    """Independent verification adapter for the SHUUD application domain."""

    def __init__(self, verifier: IndependentVerifier | None = None):
        self._verifier = verifier or IndependentVerifier()

    def verify_bundle(self, bundle: Dict[str, Any]) -> SHUUDVerificationResult:
        reasons: list[str] = []

        if not self._verifier.verify_bundle(bundle):
            return SHUUDVerificationResult(False, ("GERCHAIN_BUNDLE_INVALID",))

        entries = bundle.get("entries", [])
        shuud_entries = []
        incident_ids: set[str] = set()
        escrow_ids: set[str] = set()
        decision_values: list[str] = []
        event_types: list[str] = []

        for entry in entries:
            record = entry.get("record", {})
            payload = entry.get("event_payload", {})
            if payload.get("domain") != "SHUUD":
                continue

            incident_id = payload.get("incident_id")
            if not isinstance(incident_id, str) or not incident_id:
                reasons.append("SHUUD_INCIDENT_ID_MISSING")
                continue

            incident_ids.add(incident_id)
            event_type = payload.get("event_type")
            event_types.append(event_type)
            shuud_entries.append(entry)

            inner = payload.get("payload", {})
            if event_type == "SHIID_DECISION":
                decision_values.append(inner.get("decision"))
            if event_type == "SHUUD_RELEASE_AUTHORIZED":
                escrow_id = inner.get("escrow_id")
                if isinstance(escrow_id, str) and escrow_id:
                    escrow_ids.add(escrow_id)
                else:
                    reasons.append("ESCROW_ID_MISSING")

            if record.get("event_type") != event_type:
                reasons.append("EVENT_TYPE_MISMATCH")

        if not shuud_entries:
            reasons.append("NO_SHUUD_EVENTS")
            return SHUUDVerificationResult(False, tuple(reasons))

        if len(incident_ids) != 1:
            reasons.append("MULTIPLE_OR_MISSING_INCIDENT_IDS")

        required = {
            "SHUUD_EVIDENCE_LOCKED",
            "SHIID_DECISION",
            "SHUUD_RELEASE_AUTHORIZED",
        }
        if not required.issubset(set(event_types)):
            reasons.append("SHUUD_LIFECYCLE_INCOMPLETE")

        if decision_values != ["APPROVE"]:
            reasons.append("SHIID_APPROVAL_INVALID")

        if len(escrow_ids) != 1:
            reasons.append("ESCROW_REFERENCE_INVALID")

        # Release must be the final escrow transition represented by the
        # witness bundle. SHUUD itself never authorizes money movement.
        escrow_events = [
            e for e in entries
            if e.get("record", {}).get("event_type") == "ESCROW_TRANSITION"
        ]
        if not escrow_events:
            reasons.append("NO_ESCROW_TRANSITIONS")
        else:
            final_payload = escrow_events[-1].get("event_payload", {})
            target_state = final_payload.get("target_state")
            if target_state != "RELEASED":
                reasons.append("ESCROW_NOT_RELEASED")

        incident_id = next(iter(incident_ids), None)
        escrow_id = next(iter(escrow_ids), None)
        return SHUUDVerificationResult(
            verified=not reasons,
            reasons=tuple(reasons),
            incident_id=incident_id,
            escrow_id=escrow_id,
        )


__all__ = ["SHUUDIndependentVerifier", "SHUUDVerificationResult"]
