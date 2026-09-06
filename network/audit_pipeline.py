from network.security_signature_audit import SecuritySignatureAudit
from network.security_replay_audit import ReplayAuditEngine
from network.security_consensus_audit import ConsensusAuditEngine
from network.security_state_audit import StateAuditEngine

class UnifiedAuditPipeline:
    def __init__(self):
        self.replay_engine = ReplayAuditEngine()
        self.consensus_engine = ConsensusAuditEngine()
        self.state_engine = StateAuditEngine()

    def process_audit(self, event_data: dict) -> str:
        """
        Runs the event through all audit layers in sequence:
        1. Signature Audit
        2. Replay Audit
        3. Consensus Audit
        4. State Transition Audit
        
        Returns 'PASS' only if all checks pass. 
        Returns 'REJECTED' or 'INCONCLUSIVE' if any layer fails or lacks parameters.
        """
        # 1. Signature Audit Check
        try:
            message = event_data.get("message") or event_data.get("payload")
            signature = event_data.get("signature")
            public_key = event_data.get("public_key")

            if message is None or signature is None or not public_key:
                return "INCONCLUSIVE"

            sig_record = {
                "message": message,
                "signature": signature,
                "public_key": public_key
            }
            
            sig_res = SecuritySignatureAudit.audit(sig_record)
            sig_status = sig_res.get("status", "INCONCLUSIVE")
        except Exception:
            sig_status = "INCONCLUSIVE"

        if sig_status != "PASS":
            return sig_status

        # 2. Replay Audit Check
        replay_result = self.replay_engine.audit_event(
            event_data.get("event_id") or event_data.get("event_hash"), 
            event_data.get("event_hash"), 
            event_data.get("nonce")
        )
        if replay_result != "PASS":
            return replay_result

        # 3. Consensus Audit Check
        consensus_result = self.consensus_engine.audit_consensus(
            event_data.get("approvals_count"), 
            event_data.get("required_quorum")
        )
        if consensus_result != "PASS":
            return consensus_result

        # 4. State Transition Audit Check
        state_result = self.state_engine.audit_transition(
            event_data.get("current_state"), 
            event_data.get("next_state")
        )
        if state_result != "PASS":
            return state_result

        return "PASS"