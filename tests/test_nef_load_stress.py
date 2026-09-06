import pytest
from network.transaction_manager import TransactionManager
from network.nef_state_engine import NEFStateEngine

def test_nef_load_stress_throughput():
    nef_engine = NEFStateEngine(static_pool=10000.0, dynamic_limit=5000.0)
    manager = TransactionManager(state_engine=nef_engine)
    
    success_count = 0
    total_txs = 50
    for i in range(total_txs):
        tx_id = f"tx_load_{i:03d}"
        amount = 10.0
        if manager.create_transaction(tx_id, amount):
            if manager.lock_transaction(tx_id):
                if manager.release_transaction(tx_id):
                    success_count += 1
                    
    assert success_count == total_txs
    assert manager.get_transaction_status("tx_load_049") == "RELEASED"
