import pytest
from network.consensus import MultiNodeConsensus
from network.authorization import AuthorizedWitnessRegistry
from network.nef_state_engine import NEFStateEngine

def test_nef_fault_tolerance_quorum_failure():
    # 1. Эрхжүүлсэн зангилаадыг үүсгэх
    auth_registry = AuthorizedWitnessRegistry()
    node_ids = ["node_a", "node_b", "node_c"]
    for nid in node_ids:
        auth_registry.add(nid)

    # Quorum-ийг 2 гэж тохируулах (Хамгийн багадаа 2 зангилаа зөвшөөрөх ёстой)
    consensus = MultiNodeConsensus(authorization_registry=auth_registry, quorum=2)
    nef_engine = NEFStateEngine(static_pool=1000.0, dynamic_limit=500.0)

    tx_amount = 100.0
    is_valid = nef_engine.validate_transaction("tx_fault_01", tx_amount)

    # 2. Зангилаануудын нэг нь алдаатай эсвэл тасарсан (verified=False эсвэл nef_valid=False) гэж үзье
    node_results = [
        {"node_id": "node_a", "authorized": True, "verified": True, "nef_valid": is_valid, "chain_tip": "tip_1"},
        {"node_id": "node_b", "authorized": True, "verified": False, "nef_valid": False, "chain_tip": "tip_bad"}, # Сааталтай зангилаа
        {"node_id": "node_c", "authorized": True, "verified": True, "nef_valid": is_valid, "chain_tip": "tip_1"}
    ]

    result = consensus.determine_consensus(node_results)

    # node_a болон node_c гэсэн 2 зангилаа амжилттай тул кворумд хүрэх ёстой
    assert result["consensus"] == "QUORUM_REACHED"
    assert result["count"] == 2

def test_nef_fault_tolerance_below_quorum():
    auth_registry = AuthorizedWitnessRegistry()
    node_ids = ["node_a", "node_b", "node_c"]
    for nid in node_ids:
        auth_registry.add(nid)

    consensus = MultiNodeConsensus(authorization_registry=auth_registry, quorum=2)
    nef_engine = NEFStateEngine(static_pool=1000.0, dynamic_limit=500.0)

    is_valid = nef_engine.validate_transaction("tx_fault_02", 100.0)

    # Зөвхөн 1 л зангилаа амжилттай ажиллаж, бусад нь унасан тохиолдол (Quorum-д хүрэхгүй)
    node_results = [
        {"node_id": "node_a", "authorized": True, "verified": True, "nef_valid": is_valid, "chain_tip": "tip_1"},
        {"node_id": "node_b", "authorized": True, "verified": False, "nef_valid": False, "chain_tip": "tip_bad"},
        {"node_id": "node_c", "authorized": True, "verified": False, "nef_valid": False, "chain_tip": "tip_bad"}
    ]

    result = consensus.determine_consensus(node_results)

    # Кворумын босгонд хүрэхгүй тул QUORUM_REACHED гарахгүй байх ёстой
    assert result["consensus"] != "QUORUM_REACHED"
