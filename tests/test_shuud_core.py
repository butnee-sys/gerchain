from datetime import datetime, timezone

import pytest

from shuud.incident import create_incident
from shuud.policy import GateStatus, PolicyInput
from shuud.shiid import Decision, decide
from shuud.verify import verify_incident


def _pass_policy():
    return PolicyInput(
        two_party_consent=GateStatus.PASS,
        vehicle_identity_verified=GateStatus.PASS,
        timestamp_location_verified=GateStatus.PASS,
        media_complete=GateStatus.PASS,
        no_injury=GateStatus.PASS,
        no_third_party_property_damage=GateStatus.PASS,
        damage_estimate_mnt=1_500_000,
        dispute_present=GateStatus.PASS,
        fraud_flag=GateStatus.PASS,
        insurance_valid=GateStatus.PASS,
        beneficiary_valid=GateStatus.PASS,
        witness_verified=GateStatus.PASS,
    )


def test_shuud_approve_requires_explicit_policy_gates():
    incident = create_incident("Ulaanbaatar", occurred_at=datetime.now(timezone.utc))
    verification = verify_incident(incident, ["EVIDENCE-001"])
    decision = decide(incident, verification, policy=_pass_policy())

    assert verification.verified is True
    assert decision.decision is Decision.APPROVE


def test_shiid_defaults_to_human_review_when_policy_is_unknown():
    incident = create_incident("Ulaanbaatar")
    verification = verify_incident(incident, ["EVIDENCE-001"])
    decision = decide(incident, verification)

    assert verification.verified is True
    assert decision.decision is Decision.HUMAN_REVIEW
    assert "TWO_PARTY_CONSENT_UNKNOWN" in decision.reasons


def test_shiid_never_approves_without_evidence():
    incident = create_incident("Ulaanbaatar")
    verification = verify_incident(incident, [])
    decision = decide(incident, verification, policy=_pass_policy())

    assert verification.verified is False
    assert decision.decision is Decision.HUMAN_REVIEW
    assert "VERIFICATION_INCOMPLETE" in decision.reasons


def test_verification_cannot_be_applied_to_other_incident():
    incident_a = create_incident("Ulaanbaatar")
    incident_b = create_incident("Ulaanbaatar")
    verification = verify_incident(incident_a, ["EVIDENCE-001"])

    with pytest.raises(ValueError):
        decide(incident_b, verification, policy=_pass_policy())
