import pytest
from network.node_simulator import NodeSimulator

def test_multi_node_consensus_synchronization():
    # Setup multiple nodes in the network simulator environment
    node_a = NodeSimulator(node_id="node_alpha", required_quorum=2)
    node_b = NodeSimulator(node_id="node_beta", required_quorum=2)
    
    witnesses = ["validator_1", "validator_2", "validator_3"]
    signatures = {"validator_1": True, "validator_2": True, "validator_3": False}
    
    result_a = node_a.process_peer_consensus(witnesses, signatures)
    result_b = node_b.process_peer_consensus(witnesses, signatures)
    
    assert result_a == "CONSENSUS_ACCEPTED"
    assert result_b == "CONSENSUS_ACCEPTED"
    assert result_a == result_b