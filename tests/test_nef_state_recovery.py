import pytest
from network.nef_state_engine import NEFStateEngine

def test_nef_state_persistence_and_recovery():
    engine = NEFStateEngine(static_pool=5000.0, dynamic_limit=2000.0)
    assert engine.validate_transaction("tx_rec_1", 500.0) is True
    
    # Төлөвийн өгөгдлийг хадгалах болон шинэ engine рүү шилжүүлэх
    pool_val = engine.static_pool
    limit_val = engine.dynamic_limit
    
    recovered_engine = NEFStateEngine(static_pool=pool_val, dynamic_limit=limit_val)
    assert recovered_engine.validate_transaction("tx_rec_2", 100.0) is True
