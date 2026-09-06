class ConsensusAuditEngine:
    def __init__(self, required_quorum=None):
        self.default_quorum = required_quorum

    def audit_consensus(self, arg1, arg2=None) -> str:
        """
        Audits multi-party witness consensus and quorum threshold.
        Supports both:
        - audit_consensus(approvals_count, required_quorum)
        - audit_consensus(witnesses, signatures) using self.default_quorum
        """
        # Case 1: arg2 is a dictionary of signatures
        if isinstance(arg2, dict):
            witnesses = arg1
            signatures = arg2
            
            # If witnesses list is empty or None, return INCONCLUSIVE
            if not witnesses or not signatures:
                return "INCONCLUSIVE"

            quorum = self.default_quorum
            if quorum is None:
                return "INCONCLUSIVE"
            
            # Count valid/true signatures
            valid_count = sum(1 for v in signatures.values() if v)
            try:
                q_val = int(quorum)
            except (ValueError, TypeError):
                return "INCONCLUSIVE"

            count = valid_count
        else:
            # Case 2: standard (approvals_count, required_quorum)
            approvals_count = arg1
            required_quorum = arg2 if arg2 is not None else self.default_quorum
            
            if approvals_count is None or required_quorum is None:
                return "INCONCLUSIVE"

            try:
                count = int(approvals_count)
                q_val = int(required_quorum)
            except (ValueError, TypeError):
                return "INCONCLUSIVE"

        if count < 0 or q_val < 0:
            return "INCONCLUSIVE"

        if count >= q_val:
            return "PASS"
        else:
            return "REJECTED"