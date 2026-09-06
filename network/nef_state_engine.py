class NEFStateEngine:
    def __init__(self, static_pool: float = 0.0, dynamic_limit: float = 0.0):
        self.static_pool = static_pool
        self.dynamic_limit = dynamic_limit

    def get_static_pool(self) -> float:
        return self.static_pool

    def get_dynamic_limit(self) -> float:
        return self.dynamic_limit

    def validate_transaction(self, tx_id: str, amount: float) -> bool:
        if amount <= self.static_pool and amount <= self.dynamic_limit:
            self.static_pool -= amount
            return True
        return False