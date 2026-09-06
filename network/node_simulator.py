class NodeSimulator:
    def __init__(self, node_id: str, required_quorum: int):
        self.node_id = node_id
        self.required_quorum = required_quorum
        self.ledger = []

    def process_peer_consensus(self, witnesses: list, signatures: dict) -> str:
        """
        Simulates multi-node consensus validation across the network.
        """
        if not witnesses or not signatures:
            return "INCONCLUSIVE"
            
        valid_count = sum(1 for w in witnesses if signatures.get(w, False))
        
        if valid_count >= self.required_quorum:
            return "CONSENSUS_ACCEPTED"
        else:
            return "CONSENSUS_REJECTED"