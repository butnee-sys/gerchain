"""Cross-domain invariant tests for SHUUD + GerChain WitnessChain.

These tests document the current integration contract: SHUUD milestones and
escrow transitions may share a WitnessChain, but SHUUD must never mutate the
escrow state directly. The authoritative escrow transition remains
EscrowEngine.transition().
"""

from datetime import datetime, timezone

from escrow.engine import EscrowEngine
from witness.chain import WitnessChain

from shuud.evidence import create_evidence_envelope
from shuud.witness import record_evidence_locked


def test_shuud_witness_event_does_not_directly_change_escrow_state():
    chain = WitnessChain(initial_state={"domain": "integration"})
    escrow = EscrowEngine("ESC-001", 1_500_000, "NEF", chain)

    before = escrow.get_state()
    evidence = create_evidence_envelope(
        "INC-001",
        evidence_refs=["photo-1"],
        gps_coordinates="47.918,106.917",
        captured_at="2026-09-12T00:00:10+00:00",
        vehicle_identity_refs=["vehicle-a", "vehicle-b"],
        consent_refs=["consent-a", "consent-b"],
        media_complete=True,
    )

    record_evidence_locked(
        chain,
        evidence,
        timestamp="2026-09-12T00:00:15+00:00",
    )

    after = escrow.get_state()
    assert after == before
    assert after["state"] == "CREATED"


def test_escrow_transition_remains_the_only_release_path():
    chain = WitnessChain(initial_state={"domain": "integration"})
    escrow = EscrowEngine("ESC-002", 1_500_000, "NEF", chain)

    escrow.transition("FUNDED", "2026-09-12T00:00:20+00:00", {"source": "sandbox"})
    escrow.transition("LOCKED", "2026-09-12T00:00:30+00:00", {"source": "sandbox"})

    assert escrow.get_state()["state"] == "LOCKED"

    escrow.transition(
        "RELEASED",
        datetime(2026, 9, 12, 0, 1, 0, tzinfo=timezone.utc).isoformat(),
        {"source": "authorized"},
    )

    assert escrow.get_state()["state"] == "RELEASED"
