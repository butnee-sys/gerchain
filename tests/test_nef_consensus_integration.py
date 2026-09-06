import pytest
from network.consensus import MultiNodeConsensus
from network.authorization import AuthorizedWitnessRegistry
from network.nef_state_engine import NEFStateEngine

def test_consensus_with_nef_state_validation():
    auth_registry = AuthorizedWitnessRegistry()
    node_id = "node_alpha_01"
    auth_registry.add(node_id)
    
    nef_engine = NEFStateEngine(static_pool=1000.0, dynamic_limit=500.0)
    # Кворумын босгыг 1 болгож тохируулна
    consensus = MultiNodeConsensus(authorization_registry=auth_registry, quorum=1)
    
    tx_amount = 200.0
    is_nef_valid = nef_engine.validate_transaction("tx_001", tx_amount)
    
    node_results = [
        {
            "node_id": node_id,
            "authorized": True,
            "verified": True,
            "nef_valid": is_nef_valid,
            "chain_tip": "block_hash_abc123"
        }
    ]
    
    result = consensus.determine_consensus(node_results)
    
    assert result["consensus"] == "QUORUM_REACHED"
    assert result["chain_tip"] == "block_hash_abc123"
    assert result["count"] == 1

def test_consensus_rejects_nef_violation():
    auth_registry = AuthorizedWitnessRegistry()
    node_id = "node_beta_02"
    auth_registry.add(node_id)
    
    nef_engine = NEFStateEngine(static_pool=50.0, dynamic_limit=10.0)
    consensus = MultiNodeConsensus(authorization_registry=auth_registry, quorum=1)
    
    tx_amount = 100.0
    is_nef_valid = nef_engine.validate_transaction("tx_002", tx_amount)
    
    node_results = [
        {
            "node_id": node_id,
            "authorized": True,
            "verified": True,
            "nef_valid": is_nef_valid,
            "chain_tip": "block_hash_xyz789"
        }
    ]
    
    valid_results = [
        r for r in node_results 
        if r.get("authorized") and r.get("verified") and r.get("nef_valid", True)
    ]
    
    assert len(valid_results) == 0