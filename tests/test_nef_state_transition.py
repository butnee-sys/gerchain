import pytest
from network.nef_engine import NEFStateEngine

def test_nef_full_state_lifecycle():
    engine = NEFStateEngine()
    assert engine.state == "PENDING"
    
    assert engine.transition("LOCKED") is True
    assert engine.state == "LOCKED"
    
    assert engine.transition("RELEASED") is True
    assert engine.state == "RELEASED"

def test_nef_invalid_transition():
    engine = NEFStateEngine()
    # Cannot go directly from PENDING to RELEASED
    assert engine.transition("RELEASED") is False
    assert engine.state == "PENDING"