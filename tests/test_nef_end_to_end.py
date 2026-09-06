import pytest
from network.consensus import MultiNodeConsensus
from network.authorization import AuthorizedWitnessRegistry
from network.nef_state_engine import NEFStateEngine

def test_nef_full_end_to_end_pipeline():
    # 1. Сүлжээний эрхжүүлэлт ба зангилааг бэлтгэх
    auth_registry = AuthorizedWitnessRegistry()
    node_ids = ["node_alpha_1", "node_beta_2", "node_gamma_3"]
    for nid in node_ids:
        auth_registry.add(nid)

    # 2. NEF State Engine болон Consensus байгуулах
    nef_engine = NEFStateEngine(static_pool=5000.0, dynamic_limit=2500.0)
    consensus = MultiNodeConsensus(authorization_registry=auth_registry, quorum=2)

    # 3. Бодит гүйлгээний өгөгдөл үүсгэх
    tx_id = "tx_nef_e2e_999"
    tx_amount = 450.0
    
    # NEF шалгуур амжилттай эсэхийг шалгах
    is_valid = nef_engine.validate_transaction(tx_id, tx_amount)
    assert is_valid is True

    # 4. Зангилаа бүрийн гүйцэтгэлийн үр дүнг бүрдүүлэх
    node_results = []
    shared_tip = "tip_block_hash_xyz789"
    for nid in node_ids:
        node_results.append({
            "node_id": nid,
            "authorized": True,
            "verified": True,
            "nef_valid": is_valid,
            "chain_tip": shared_tip
        })

    # 5. Консенсусын үр дүнг тодорхойлох
    consensus_result = consensus.determine_consensus(node_results)

    # 6. Шалгах
    assert consensus_result["consensus"] == "QUORUM_REACHED"
    assert consensus_result["chain_tip"] == shared_tip
    assert consensus_result["count"] >= consensus.quorum
