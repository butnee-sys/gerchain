from datetime import datetime, timezone

import pytest

from escrow.engine import EscrowEngine
from shuud.incident import create_incident
from shuud.policy import GateStatus, PolicyInput
from shuud.release import authorize_release, release_escrow
from shuud.shiid import Decision, decide
from shuud.verify import verify_incident
from witness.chain import WitnessChain


def approved_decision():
    incident = create_incident(
        "Ulaanbaatar",
        vehicle_a="1234ABC",
        vehicle_b="5678DEF",
        occurred_at=datetime.now(timezone.utc),
    )
    verification = verify_incident(incident, ["EVIDENCE-001"])
    policy = PolicyInput(
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
    return decide(incident, verification, policy=policy)


def make_locked_escrow():
    witness = WitnessChain(
        initial_state={"value": 0},
        manifest={"purpose": "SHUUD sandbox"},
        witness_id="WITNESS-ROOT-001",
    )
    escrow = EscrowEngine(
        escrow_id="SHUUD-ESCROW-001",
        amount=1_500_000,
        currency="NEF",
        witness_chain=witness,
    )
    escrow.transition("FUNDED", "2026-09-12T00:00:00+00:00", {"seed": True})
    escrow.transition("LOCKED", "2026-09-12T00:00:01+00:00", {"seed": True})
    return escrow


def test_release_requires_approved_shiid_decision():
    incident = create_incident("Ulaanbaatar")
    verification = verify_incident(incident, ["EVIDENCE-001"])
    decision = decide(incident, verification)

    assert decision.decision is Decision.HUMAN_REVIEW
    with pytest.raises(ValueError):
        authorize_release(decision, escrow_id="SHUUD-ESCROW-001")


def test_release_bridge_delegates_locked_to_released():
    decision = approved_decision()
    authorization = authorize_release(
        decision,
        escrow_id="SHUUD-ESCROW-001",
    )
    escrow = make_locked_escrow()

    record = release_escrow(
        escrow,
        authorization,
        timestamp="2026-09-12T00:00:02+00:00",
    )

    assert record.previous_state == "LOCKED"
    assert record.new_state == "RELEASED"
    assert escrow.get_state()["state"] == "RELEASED"
    assert len(escrow.witness_chain.entries) == 3


def test_release_cannot_bypass_locked_state():
    decision = approved_decision()
    authorization = authorize_release(
        decision,
        escrow_id="SHUUD-ESCROW-001",
    )
    witness = WitnessChain(
        initial_state={"value": 0},
        manifest={"purpose": "SHUUD sandbox"},
        witness_id="WITNESS-ROOT-001",
    )
    escrow = EscrowEngine(
        escrow_id="SHUUD-ESCROW-001",
        amount=1_500_000,
        currency="NEF",
        witness_chain=witness,
    )

    with pytest.raises(ValueError):
        release_escrow(escrow, authorization)
