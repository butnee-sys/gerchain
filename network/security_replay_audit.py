import hashlib
import hmac
import secrets

class ReplayAuditEngine:
    def __init__(self):
        self.seen_event_hashes = set()
        self.seen_nonces = set()

    def audit_event(self, event_id: str, event_hash: str, nonce: str) -> str:
        """
        Audits an event against replay attacks.
        Returns:
            - 'PASS' if the event is fresh and valid.
            - 'REJECTED' if the event hash or nonce has already been processed (Replay Attack).
            - 'INCONCLUSIVE' if parameters are missing or malformed.
        """
        if not event_id or not event_hash or not nonce:
            return "INCONCLUSIVE"

        # Check for replay
        if event_hash in self.seen_event_hashes or nonce in self.seen_nonces:
            return "REJECTED"

        # Mark as seen
        self.seen_event_hashes.add(event_hash)
        self.seen_nonces.add(nonce)

        return "PASS"