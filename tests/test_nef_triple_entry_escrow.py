import pytest
from network.transaction_manager import TransactionManager
from network.nef_state_engine import NEFStateEngine

def test_triple_entry_escrow_pipeline():
    # NEF State Engine-ийг тодорхой нөөцтэйгээр үүсгэх
    nef_engine = NEFStateEngine(static_pool=2000.0, dynamic_limit=1000.0)
    
    # TransactionManager-ийг NEFStateEngine-тэй холбох
    manager = TransactionManager(state_engine=nef_engine)

    tx_id = "tx_triple_escrow_01"
    amount = 300.0

    # 1. Гүйлгээ үүсгэх (PENDING) ба NEF лимитийн шалгалт
    assert manager.create_transaction(tx_id, amount) is True
    assert manager.get_transaction_status(tx_id) == "PENDING"

    # 2. Гүйлгээг түгжих (LOCKED) - Эскроу дансанд шилжүүлэх үе шат
    assert manager.lock_transaction(tx_id) is True
    assert manager.get_transaction_status(tx_id) == "LOCKED"

    # 3. Гүйлгээг амжилттай чөлөөлөх (RELEASED) - Давхар бичилт болон төлөв баталгаажих
    assert manager.release_transaction(tx_id) is True
    assert manager.get_transaction_status(tx_id) == "RELEASED"
