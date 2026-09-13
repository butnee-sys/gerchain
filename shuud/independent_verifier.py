"""SHUUD-specific verification boundary.

This module does not implement cryptography or a second witness chain. It
reuses GerChain's existing IndependentVerifier for cryptographic/state
verification and adds only SHUUD domain invariants required before release.
"""

from dataclasses import dataclass
from typing import Any, Dict

from .integration import IndependentVerifier


EXPECTED_CURRENCY = "MNT"
EXPECTED_SETTLEMENT_PROVIDER = "NEF"


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
        decision_damage_estimates: list[float | int | None] = []
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

            if event_type == "SHIID_DECISION":
                decision_values.append(payload.get("decision"))
                decision_damage_estimates.append(payload.get("damage_estimate_mnt"))

            if event_type == "SHUUD_RELEASE_AUTHORIZED":
                escrow_id = payload.get("escrow_id")
                if isinstance(escrow_id, str) and escrow_id:
                    escrow_ids.add(escrow_id)

            if record.get("currency") not in (None, EXPECTED_CURRENCY):
                reasons.append("SHUUD_CURRENCY_MISMATCH")

            settlement_provider = payload.get("settlement_provider")
            if settlement_provider not in (None, EXPECTED_SETTLEMENT_PROVIDER):
                reasons.append("SHUUD_SETTLEMENT_PROVIDER_MISMATCH")

        if not shuud_entries:
            reasons.append("SHUUD_EVENTS_MISSING")
        if len(incident_ids) > 1:
            reasons.append("SHUUD_MULTIPLE_INCIDENTS")
        if any(value is None for value in decision_values):
            reasons.append("SHUUD_DECISION_MISSING")
        if any(value is not None and float(value) < 0 for value in decision_damage_estimates):
            reasons.append("SHUUD_DAMAGE_ESTIMATE_INVALID")

        incident_id = next(iter(incident_ids), None)
        escrow_id = next(iter(escrow_ids), None)
        verified = not reasons
        return SHUUDVerificationResult(
            verified,
            tuple(reasons),
            incident_id=incident_id,
            escrow_id=escrow_id,
        )


__all__ = ["SHUUDIndependentVerifier", "SHUUDVerificationResult"]
