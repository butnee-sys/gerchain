class NEFStateEngine:
    def __init__(self):
        self.state = "PENDING"

    def transition(self, target_state: str) -> bool:
        allowed_transitions = {
            "PENDING": ["LOCKED"],
            "LOCKED": ["RELEASED", "PENDING"],
            "RELEASED": []
        }
        if target_state in allowed_transitions.get(self.state, []):
            self.state = target_state
            return True
        return False