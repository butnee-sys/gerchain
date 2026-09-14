"""SHUUD verification gate.

The verifier only evaluates application-level completeness. It does not
replace GerChain Witness/IndependentVerifier and it cannot release funds.
"""

from dataclasses import dataclass
from typing import Sequence

from .incident import Incident


@dataclass(frozen=True)
class VerificationResult:
    incident_id: str
    evidence_complete: bool
    verified: bool
    reasons: tuple[str, ...]


def verify_incident(
    incident: Incident,
    evidence_refs: Sequence[str],
) -> VerificationResult:
    reasons: list[str] = []

    if not evidence_refs:
        reasons.append("NO_EVIDENCE")

    if not incident.location:
        reasons.append("NO_LOCATION")

    verified = not reasons
    return VerificationResult(
        incident_id=incident.incident_id,
        evidence_complete=bool(evidence_refs),
        verified=verified,
        reasons=tuple(reasons),
    )


__all__ = ["VerificationResult", "verify_incident"]
