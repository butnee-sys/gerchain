from datetime import datetime, timezone

import pytest

from shuud.incident import create_incident
from shuud.shiid import Decision, decide
from shuud.verify import verify_incident


def test_shuud_approve_requires_evidence():
    incident = create_incident(
        "Ulaanbaatar",
        occurred_at=datetime.now(timezone.utc),
    )
    verification = verify_incident(incident, ["EVIDENCE-001"])
    decision = decide(incident, verification)

    assert verification.verified is True
    assert decision.decision is Decision.APPROVE


def test_shiid_never_approves_without_evidence():
    incident = create_incident("Ulaanbaatar")
    verification = verify_incident(incident, [])
    decision = decide(incident, verification)

    assert verification.verified is False
    assert decision.decision is Decision.HUMAN_REVIEW
    assert "NO_EVIDENCE" in decision.reasons


def test_verification_cannot_be_applied_to_other_incident():
    incident_a = create_incident("Ulaanbaatar")
    incident_b = create_incident("Ulaanbaatar")
    verification = verify_incident(incident_a, ["EVIDENCE-001"])

    with pytest.raises(ValueError):
        decide(incident_b, verification)
