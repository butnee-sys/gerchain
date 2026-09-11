from datetime import datetime, timezone

from shuud.incident import create_incident
from shuud.policy import GateStatus, PolicyInput, evaluate_policy
from shuud.shiid import Decision, decide
from shuud.verify import verify_incident


def approved_policy() -> PolicyInput:
    return PolicyInput(
        two_party_consent=GateStatus.PASS,
        vehicle_identity_verified=GateStatus.PASS,
        timestamp_location_verified=GateStatus.PASS,
        media_complete=GateStatus.PASS,
        no_injury=GateStatus.PASS,
        no_third_party_property_damage=GateStatus.PASS,
        damage_estimate_nef=1_500_000,
        dispute_present=GateStatus.PASS,
        fraud_flag=GateStatus.PASS,
        insurance_valid=GateStatus.PASS,
        beneficiary_valid=GateStatus.PASS,
        witness_verified=GateStatus.PASS,
    )


def test_policy_approves_only_when_all_gates_pass():
    incident = create_incident(
        "Ulaanbaatar",
        occurred_at=datetime.now(timezone.utc),
    )
    verification = verify_incident(incident, ["EVIDENCE-001"])
    result = evaluate_policy(incident, verification, approved_policy())

    assert result.eligible is True
    assert result.reasons == ()

    decision = decide(incident, verification, policy=approved_policy())
    assert decision.decision is Decision.APPROVE


def test_policy_fails_closed_on_unknown_gate():
    incident = create_incident("Ulaanbaatar")
    verification = verify_incident(incident, ["EVIDENCE-001"])
    result = evaluate_policy(incident, verification, PolicyInput())

    assert result.eligible is False
    assert "TWO_PARTY_CONSENT_UNKNOWN" in result.reasons

    decision = decide(incident, verification, policy=PolicyInput())
    assert decision.decision is Decision.HUMAN_REVIEW


def test_policy_rejects_damage_above_sandbox_limit():
    incident = create_incident("Ulaanbaatar")
    verification = verify_incident(incident, ["EVIDENCE-001"])
    policy = approved_policy()
    policy = PolicyInput(**{**policy.__dict__, "damage_estimate_nef": 2_000_001})

    result = evaluate_policy(incident, verification, policy)

    assert result.eligible is False
    assert "DAMAGE_LIMIT_EXCEEDED" in result.reasons
