from __future__ import annotations

import pytest

from escrow.engine import EscrowEngine
from witness.chain import WitnessChain


def _engine() -> EscrowEngine:
    witness = WitnessChain(
        initial_state={"status": "OPEN"},
        manifest={"version": 1},
        witness_id="W-1",
    )
    return EscrowEngine("ESC-GATE-1", 100, "NEF", witness)


def test_terminal_escrow_transition_requires_dee_root_and_trinity() -> None:
    escrow = _engine()
    with pytest.raises(ValueError, match="Root of Trust and Trinity proof"):
        escrow.transition(
            "RELEASED",
            "2026-09-14T00:00:00Z",
            {"case": "INC-1"},
        )


def test_non_terminal_transition_keeps_deterministic_state_machine() -> None:
    escrow = _engine()
    record = escrow.transition(
        "FUNDED",
        "2026-09-14T00:00:00Z",
        {"funding": "verified"},
    )
    assert record.new_state == "FUNDED"
    assert escrow.get_state()["state"] == "FUNDED"
