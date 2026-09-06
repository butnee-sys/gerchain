class TransactionManager:
    def __init__(self, audit_logger=None, state_engine=None):
        self.transactions = {}
        self.audit_logger = audit_logger
        self.state_engine = state_engine

    def create_transaction(self, tx_id: str, amount: float) -> bool:
        if tx_id in self.transactions:
            return False
        
        # StateEngine ашиглан лимит болон балансыг шалгах
        if self.state_engine and hasattr(self.state_engine, "validate_transaction"):
            if not self.state_engine.validate_transaction(tx_id, amount):
                return False

        self.transactions[tx_id] = {"amount": amount, "status": "PENDING"}
        if self.audit_logger:
            self.audit_logger.log(f"CREATED: {tx_id} with amount {amount}")
        return True

    def get_transaction_status(self, tx_id: str) -> str:
        return self.transactions.get(tx_id, {}).get("status", "NOT_FOUND")

    def lock_transaction(self, tx_id: str) -> bool:
        tx = self.transactions.get(tx_id)
        if tx and tx["status"] == "PENDING":
            tx["status"] = "LOCKED"
            if self.audit_logger:
                self.audit_logger.log(f"LOCKED: {tx_id}")
            return True
        return False

    def release_transaction(self, tx_id: str) -> bool:
        tx = self.transactions.get(tx_id)
        if tx and tx["status"] == "LOCKED":
            tx["status"] = "RELEASED"
            if self.audit_logger:
                self.audit_logger.log(f"RELEASED: {tx_id}")
            return True
        return False

    def cancel_transaction(self, tx_id: str) -> bool:
        tx = self.transactions.get(tx_id)
        if tx and tx["status"] in ("PENDING", "LOCKED"):
            tx["status"] = "CANCELLED"
            if self.audit_logger:
                self.audit_logger.log(f"CANCELLED: {tx_id}")
            return True
        return False