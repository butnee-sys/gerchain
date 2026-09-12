"""SHUUD-specific verification boundary.

This module does not implement cryptography or a second witness chain. It
reuses GerChain's existing IndependentVerifier for cryptographic/state
verification and adds only SHUUD domain invariants required before release.
"""

from dataclasses import dataclass
from typing import Any, Dict

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
        decision_incident_ids: list[str] = []
        escrow_ids: set[str] = set()
        decision_values: list[str] = []
        decision_damage_estimates: list[float | int | None] = []
        event_types: list[str] = []

        manifest = bundle.get("manifest", {})
        manifest_incident_id = manifest.get("incident_id")
        canonical_incident_id = (
            manifest_incident_id if isinstance(manifest_incident_id, str) and manifest_incident_id else None
        )

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

            if canonical_incident_id is not None and incident_id != canonical_incident_id:
                reasons.append("INCIDENT_ID_MISMATCH")

            inner = payload.get("payload", {})
            if event_type == "SHIID_DECISION":
                decision_values.append(inner.get("decision"))
                decision_damage_estimates.append(inner.get("damage_estimate_nef"))
                decision_incident_ids.append(incident_id)

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

        if canonical_incident_id is None and len(incident_ids) == 1:
            canonical_incident_id = next(iter(incident_ids))

        if len(decision_incident_ids) != 1 or (
            canonical_incident_id is not None
            and decision_incident_ids[0] != canonical_incident_id
        ):
            reasons.append("INCIDENT_ID_MISMATCH")

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

        escrow_events = [
            e for e in entries
            if e.get("record", {}).get("event_type") == "ESCROW_TRANSITION"
        ]
        if not escrow_events:
            reasons.append("NO_ESCROW_TRANSITIONS")
        else:
            expected_path = [
                ("CREATED", "FUNDED"),
                ("FUNDED", "LOCKED"),
                ("LOCKED", "RELEASED"),
            ]
            actual_path = []
            escrow_transition_ids: set[str] = set()
            escrow_amounts: set[float | int] = set()
            for entry in escrow_events:
                payload = entry.get("event_payload", {})
                actual_path.append(
                    (payload.get("previous_state"), payload.get("new_state"))
                )
                escrow_id = payload.get("escrow_id")
                if isinstance(escrow_id, str) and escrow_id:
                    escrow_transition_ids.add(escrow_id)
                amount = payload.get("amount")
                if isinstance(amount, (int, float)) and not isinstance(amount, bool):
                    escrow_amounts.add(amount)

            if actual_path != expected_path:
                reasons.append("ESCROW_LIFECYCLE_INVALID")

            if len(escrow_transition_ids) != 1 or escrow_transition_ids != escrow_ids:
                reasons.append("ESCROW_ID_MISMATCH")

            decision_amount = (
                decision_damage_estimates[0]
                if len(decision_damage_estimates) == 1
                else None
            )
            if (
                len(decision_damage_estimates) != 1
                or isinstance(decision_amount, bool)
                or not isinstance(decision_amount, (int, float))
                or len(escrow_amounts) != 1
            ):
                reasons.append("ESCROW_AMOUNT_REFERENCE_INVALID")
            elif decision_amount != next(iter(escrow_amounts)):
                reasons.append("ESCROW_AMOUNT_MISMATCH")

            final_payload = escrow_events[-1].get("event_payload", {})
            if final_payload.get("new_state") != "RELEASED":
                reasons.append("ESCROW_NOT_RELEASED")

        incident_id = canonical_incident_id or next(iter(incident_ids), None)
        escrow_id = next(iter(escrow_ids), None)
        return SHUUDVerificationResult(
            verified=not reasons,
            reasons=tuple(dict.fromkeys(reasons)),
            incident_id=incident_id,
            escrow_id=escrow_id,
        )


__all__ = ["SHUUDIndependentVerifier", "SHUUDVerificationResult"]
