import pytest
from network.transaction_manager import TransactionManager
from network.nef_state_engine import NEFStateEngine

class CustomAuditLogger:
    def __init__(self):
        self.records = []
    def log(self, message: str):
        self.records.append(message)

def test_nef_audit_pipeline_integration():
    logger = CustomAuditLogger()
    nef_engine = NEFStateEngine(static_pool=2000.0, dynamic_limit=1000.0)
    manager = TransactionManager(audit_logger=logger, state_engine=nef_engine)
    
    tx_id = "tx_audit_01"
    assert manager.create_transaction(tx_id, 150.0) is True
    assert manager.lock_transaction(tx_id) is True
    assert manager.release_transaction(tx_id) is True
    
    # Аудитын бүртгэлд бүх төлөв шилжилт амжилттай бичигдсэнийг шалгах
    assert any("CREATED: tx_audit_01" in r for r in logger.records)
    assert any("LOCKED: tx_audit_01" in r for r in logger.records)
    assert any("RELEASED: tx_audit_01" in r for r in logger.records)
