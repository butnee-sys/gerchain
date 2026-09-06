import pytest
from network.transaction_manager import TransactionManager

class MockAuditLogger:
    def __init__(self):
        self.logs = []

    def log(self, message: str):
        self.logs.append(message)

class MockStateEngine:
    def __init__(self, allow_validation=True):
        self.allow_validation = allow_validation

    def validate_transaction(self, tx_id: str, amount: float) -> bool:
        return self.allow_validation

def test_transaction_creation():
    manager = TransactionManager()
    assert manager.create_transaction("tx_001", 100.0) is True
    assert manager.get_transaction_status("tx_001") == "PENDING"

def test_duplicate_transaction():
    manager = TransactionManager()
    assert manager.create_transaction("tx_001", 100.0) is True
    assert manager.create_transaction("tx_001", 50.0) is False

def test_transaction_lifecycle():
    manager = TransactionManager()
    manager.create_transaction("tx_002", 250.0)
    
    # Lock transition
    assert manager.lock_transaction("tx_002") is True
    assert manager.get_transaction_status("tx_002") == "LOCKED"
    
    # Release transition
    assert manager.release_transaction("tx_002") is True
    assert manager.get_transaction_status("tx_002") == "RELEASED"

def test_invalid_state_transitions():
    manager = TransactionManager()
    manager.create_transaction("tx_003", 500.0)
    
    # Cannot release directly from PENDING without locking first
    assert manager.release_transaction("tx_003") is False
    assert manager.get_transaction_status("tx_003") == "PENDING"
    
    # Lock first
    assert manager.lock_transaction("tx_003") is True
    # Cannot lock an already locked transaction
    assert manager.lock_transaction("tx_003") is False

def test_cancel_transaction():
    manager = TransactionManager()
    manager.create_transaction("tx_004", 300.0)
    
    # Cancel from PENDING
    assert manager.cancel_transaction("tx_004") is True
    assert manager.get_transaction_status("tx_004") == "CANCELLED"
    
    # Test cancelling a LOCKED transaction
    manager.create_transaction("tx_005", 150.0)
    assert manager.lock_transaction("tx_005") is True
    assert manager.cancel_transaction("tx_005") is True
    assert manager.get_transaction_status("tx_005") == "CANCELLED"
    
    # Cannot cancel an already RELEASED or CANCELLED transaction
    manager.create_transaction("tx_006", 400.0)
    assert manager.lock_transaction("tx_006") is True
    assert manager.release_transaction("tx_006") is True
    assert manager.cancel_transaction("tx_006") is False

def test_transaction_audit_logging():
    logger = MockAuditLogger()
    manager = TransactionManager(audit_logger=logger)
    
    manager.create_transaction("tx_100", 1000.0)
    manager.lock_transaction("tx_100")
    manager.release_transaction("tx_100")
    
    assert "CREATED: tx_100 with amount 1000.0" in logger.logs
    assert "LOCKED: tx_100" in logger.logs
    assert "RELEASED: tx_100" in logger.logs
    assert len(logger.logs) == 3

def test_state_engine_validation():
    # StateEngine амжилттай зөвшөөрөх тохиолдол
    engine_pass = MockStateEngine(allow_validation=True)
    manager = TransactionManager(state_engine=engine_pass)
    assert manager.create_transaction("tx_200", 500.0) is True
    assert manager.get_transaction_status("tx_200") == "PENDING"

    # StateEngine буюу ресурс хүрэлцэхгүй гэж татгалзах тохиолдол
    engine_fail = MockStateEngine(allow_validation=False)
    manager_fail = TransactionManager(state_engine=engine_fail)
    assert manager_fail.create_transaction("tx_201", 5000.0) is False
    assert manager_fail.get_transaction_status("tx_201") == "NOT_FOUND"