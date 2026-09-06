import pytest
from network.nef_state_engine import NEFStateEngine

def test_nef_engine_initialization():
    engine = NEFStateEngine(static_pool=10000.0, dynamic_limit=5000.0)
    assert engine.get_static_pool() == 10000.0
    assert engine.get_dynamic_limit() == 5000.0

def test_validate_transaction_within_limits():
    engine = NEFStateEngine(static_pool=10000.0, dynamic_limit=5000.0)
    assert engine.validate_transaction("tx_01", 1000.0) is True

def test_validate_transaction_exceeds_limits():
    engine = NEFStateEngine(static_pool=1000.0, dynamic_limit=500.0)
    assert engine.validate_transaction("tx_02", 2000.0) is False

def test_pool_depletion_after_successful_transaction():
    engine = NEFStateEngine(static_pool=5000.0, dynamic_limit=3000.0)
    assert engine.validate_transaction("tx_03", 2000.0) is True
    assert engine.get_static_pool() == 3000.0

def test_multiple_transactions_pool_tracking():
    engine = NEFStateEngine(static_pool=4000.0, dynamic_limit=4000.0)
    assert engine.validate_transaction("tx_04", 1500.0) is True
    assert engine.get_static_pool() == 2500.0
    
    # Үлдэгдэл хүрэлцэхгүй тул амжилтгүй болох ёстой
    assert engine.validate_transaction("tx_05", 3000.0) is False
    assert engine.get_static_pool() == 2500.0  # Амжилтгүй болвол пул өөрчлөгдөхгүй