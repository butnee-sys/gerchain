"""SHIID decision layer.

SHIID decides only whether an incident is eligible for the next workflow
step. It has no direct authority over money, escrow, or GerChain state.
"""

from dataclasses import dataclass
from enum import Enum

from .incident import Incident
from .verify import VerificationResult


class Decision(str, Enum):
    APPROVE = "APPROVE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    REJECT = "REJECT"


@dataclass(frozen=True)
class SHIIDDecision:
    incident_id: str
    decision: Decision
    rule_version: str
    reasons: tuple[str, ...]


def decide(
    incident: Incident,
    verification: VerificationResult,
    *,
    rule_version: str = "SHIID-0.1",
) -> SHIIDDecision:
    if verification.incident_id != incident.incident_id:
        raise ValueError("verification does not belong to incident")

    if not verification.verified:
        return SHIIDDecision(
            incident_id=incident.incident_id,
            decision=Decision.HUMAN_REVIEW,
            rule_version=rule_version,
            reasons=verification.reasons,
        )

    return SHIIDDecision(
        incident_id=incident.incident_id,
        decision=Decision.APPROVE,
        rule_version=rule_version,
        reasons=("VERIFICATION_COMPLETE",),
    )


__all__ = ["Decision", "SHIIDDecision", "decide"]
