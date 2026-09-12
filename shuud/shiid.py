"""SHIID decision layer.

SHIID decides only whether an incident is eligible for the next workflow
step. It has no direct authority over money, escrow, or GerChain state.
"""

from dataclasses import dataclass
from enum import Enum

from .incident import Incident
from .policy import PolicyInput, evaluate_policy
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
    damage_estimate_nef: float | None = None


def decide(
    incident: Incident,
    verification: VerificationResult,
    *,
    policy: PolicyInput | None = None,
    rule_version: str = "SHIID-0.2",
) -> SHIIDDecision:
    if verification.incident_id != incident.incident_id:
        raise ValueError("verification does not belong to incident")

    if policy is None:
        policy = PolicyInput()

    result = evaluate_policy(
        incident,
        verification,
        policy,
        rule_version=rule_version,
    )

    if result.eligible:
        return SHIIDDecision(
            incident_id=incident.incident_id,
            decision=Decision.APPROVE,
            rule_version=result.rule_version,
            reasons=("ALL_POLICY_GATES_PASSED",),
            damage_estimate_nef=policy.damage_estimate_nef,
        )

    return SHIIDDecision(
        incident_id=incident.incident_id,
        decision=Decision.HUMAN_REVIEW,
        rule_version=result.rule_version,
        reasons=result.reasons,
        damage_estimate_nef=policy.damage_estimate_nef,
    )


__all__ = ["Decision", "SHIIDDecision", "decide"]
