"""SHIID policy gates for the SHUUD sandbox.

Policy is fail-closed: an incident is APPROVE-eligible only when every
mandatory gate is explicitly satisfied. This layer never moves money and
never replaces GerChain witness/verification.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .incident import Incident
from .verify import VerificationResult


class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class PolicyInput:
    two_party_consent: GateStatus = GateStatus.UNKNOWN
    vehicle_identity_verified: GateStatus = GateStatus.UNKNOWN
    timestamp_location_verified: GateStatus = GateStatus.UNKNOWN
    media_complete: GateStatus = GateStatus.UNKNOWN
    no_injury: GateStatus = GateStatus.UNKNOWN
    no_third_party_property_damage: GateStatus = GateStatus.UNKNOWN
    damage_estimate_mnt: Optional[float] = None
    dispute_present: GateStatus = GateStatus.UNKNOWN
    fraud_flag: GateStatus = GateStatus.UNKNOWN
    insurance_valid: GateStatus = GateStatus.UNKNOWN
    beneficiary_valid: GateStatus = GateStatus.UNKNOWN
    witness_verified: GateStatus = GateStatus.UNKNOWN


@dataclass(frozen=True)
class PolicyResult:
    eligible: bool
    reasons: tuple[str, ...]
    rule_version: str


DEFAULT_MAX_DAMAGE_MNT = 2_000_000.0


def evaluate_policy(
    incident: Incident,
    verification: VerificationResult,
    policy: PolicyInput,
    *,
    rule_version: str = "SHIID-0.2",
    max_damage_mnt: float = DEFAULT_MAX_DAMAGE_MNT,
) -> PolicyResult:
    reasons: list[str] = []

    if verification.incident_id != incident.incident_id:
        raise ValueError("verification does not belong to incident")

    if not verification.verified:
        reasons.append("VERIFICATION_INCOMPLETE")

    gates = {
        "TWO_PARTY_CONSENT_REQUIRED": policy.two_party_consent,
        "VEHICLE_IDENTITY_REQUIRED": policy.vehicle_identity_verified,
        "TIME_LOCATION_REQUIRED": policy.timestamp_location_verified,
        "MEDIA_REQUIRED": policy.media_complete,
        "NO_INJURY_REQUIRED": policy.no_injury,
        "NO_THIRD_PARTY_PROPERTY_DAMAGE_REQUIRED": policy.no_third_party_property_damage,
        "DISPUTE_MUST_BE_ABSENT": policy.dispute_present,
        "FRAUD_FLAG_MUST_BE_ABSENT": policy.fraud_flag,
        "INSURANCE_MUST_BE_VALID": policy.insurance_valid,
        "BENEFICIARY_MUST_BE_VALID": policy.beneficiary_valid,
        "WITNESS_VERIFICATION_REQUIRED": policy.witness_verified,
    }

    for reason, status in gates.items():
        if status is GateStatus.PASS:
            continue
        if status is GateStatus.FAIL:
            reasons.append(reason.replace("_REQUIRED", "_FAILED"))
        else:
            reasons.append(reason.replace("_REQUIRED", "_UNKNOWN"))

    if policy.damage_estimate_mnt is None:
        reasons.append("DAMAGE_ESTIMATE_UNKNOWN")
    elif policy.damage_estimate_mnt < 0:
        reasons.append("DAMAGE_ESTIMATE_INVALID")
    elif policy.damage_estimate_mnt > max_damage_mnt:
        reasons.append("DAMAGE_LIMIT_EXCEEDED")

    return PolicyResult(
        eligible=not reasons,
        reasons=tuple(reasons),
        rule_version=rule_version,
    )


__all__ = [
    "GateStatus",
    "PolicyInput",
    "PolicyResult",
    "DEFAULT_MAX_DAMAGE_MNT",
    "evaluate_policy",
]
