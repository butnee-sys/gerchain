import pytest
from network.audit_logger import AuditLogger

def test_audit_logger_recording():
    logger = AuditLogger()
    assert logger.get_log_count() == 0
    
    logger.record_event("TX_LOCKED", "Transaction ID 101 locked successfully.")
    assert logger.get_log_count() == 1
    assert logger.logs[0]["event"] == "TX_LOCKED"

def test_audit_logger_multiple_events():
    logger = AuditLogger()
    logger.record_event("TX_PENDING", "Created transaction")
    logger.record_event("TX_RELEASED", "Released funds from escrow")
    
    assert logger.get_log_count() == 2
    assert logger.logs[1]["event"] == "TX_RELEASED"