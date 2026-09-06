class StateAuditEngine:
    def __init__(self):
        # Define valid state transition graph for escrow/events
        self.valid_transitions = {
            "PENDING": ["LOCKED", "CANCELLED"],
            "LOCKED": ["RELEASED", "REFUNDED"],
            "RELEASED": [],
            "REFUNDED": [],
            "CANCELLED": []
        }

    def audit_transition(self, current_state: str, next_state: str) -> str:
        """
        Audits state transitions to ensure invariant safety.
        Returns:
            - 'PASS' if the transition is valid.
            - 'REJECTED' if the transition violates invariants.
            - 'INCONCLUSIVE' if parameters are missing or malformed.
        """
        if not current_state or not next_state:
            return "INCONCLUSIVE"
        
        if current_state not in self.valid_transitions or next_state not in self.valid_transitions:
            return "INCONCLUSIVE"

        if next_state in self.valid_transitions[current_state]:
            return "PASS"
        else:
            return "REJECTED"