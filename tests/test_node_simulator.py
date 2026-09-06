import pytest
from network.node_simulator import NodeSimulator

def test_node_simulator_consensus_accepted():
    node = NodeSimulator(node_id="node_001", required_quorum=2)
    witnesses = ["w1", "w2", "w3"]
    signatures = {"w1": True, "w2": True, "w3": False}
    
    result = node.process_peer_consensus(witnesses, signatures)
    assert result == "CONSENSUS_ACCEPTED"

def test_node_simulator_consensus_rejected():
    node = NodeSimulator(node_id="node_001", required_quorum=3)
    witnesses = ["w1", "w2", "w3"]
    signatures = {"w1": True, "w2": False, "w3": False}
    
    result = node.process_peer_consensus(witnesses, signatures)
    assert result == "CONSENSUS_REJECTED"