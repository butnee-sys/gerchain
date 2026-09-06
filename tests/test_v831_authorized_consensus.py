"""
GerChain V83.1
Authorized Witness + Cryptographic Consensus Integration Tests.

Purpose:
- V83.0 authorization layer-ийг шалгах.
- Зөвшөөрөгдсөн node-ууд consensus-д оролцох боломжтой байх.
- Зөвшөөрөгдөөгүй node нь хүчинтэй bundle-тэй байсан ч
  authorization түвшинд хасагдах.
- Authorization ба cryptographic verification-ийг тусад нь шалгах.
- Нэг node-ийн зөвшөөрлийг цуцлахад consensus оролцоо өөрчлөгдөх.
- V82.1-ийн Chain Tip логик өөрчлөгдөөгүйг баталгаажуулах.

NOTE:
- Энэ тест одоогоор V83.0 registry + V82.1 consensus-ийг
  интеграцийн түвшинд шалгана.
- V83.1 production consensus implementation-ийг хараахан
  өөрчлөхгүй.
"""

from __future__ import annotations

import copy
import json

from core.hashing import domain_hash
from network.authorization import (
    AuthorizedWitnessRegistry,
)
from network.consensus import (
    MultiNodeConsensus,
)
from witness.chain import WitnessChain
from persistence.serializer import serialize_chain


def build_bundle(
    witness_id: str,
    buyer_balance: int = 1000,
):
    """
    V82.1/V83.1 integration test-д ашиглах
    хүчинтэй Witness Bundle үүсгэнэ.
    """

    money_state = {
        "currency": "MNT",
        "balances": {
            "BUYER": buyer_balance,
            "SELLER": 0,
        },
    }

    chain = WitnessChain(
        initial_state={
            "value": 0,
            "sequence_counter": 0,
            "initialized": False,
        },
        manifest={
            "system": "GerChain",
            "version": "V83.1",
            "purpose": "Authorized Consensus",
        },
        witness_id=witness_id,
        initial_money_state=money_state,
    )

    state_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        money_state,
    )

    chain.append_event(
        event_id="V831-INITIAL-MONEY-001",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T16:00:01",
        payload={
            "state": money_state,
            "state_hash": state_hash,
        },
        evidence={
            "type": "INITIAL_MONEY_COMMITMENT",
            "reference": "V831-001",
        },
    )

    return json.loads(
        serialize_chain(
            chain
        ).decode("utf-8")
    )


def test_authorized_nodes_can_be_registered():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
            "NODE-C",
        ]
    )

    assert registry.count() == 3

    assert registry.is_authorized(
        "NODE-A"
    )

    assert registry.is_authorized(
        "NODE-B"
    )

    assert registry.is_authorized(
        "NODE-C"
    )


def test_unauthorized_node_is_not_authorized():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    assert registry.is_authorized(
        "NODE-A"
    )

    assert registry.is_authorized(
        "NODE-B"
    )

    assert not registry.is_authorized(
        "NODE-X"
    )


def test_authorized_nodes_have_valid_cryptographic_bundle():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    bundle = build_bundle(
        "NODE-A"
    )

    consensus = MultiNodeConsensus(
        quorum=1
    )

    assert registry.is_authorized(
        "NODE-A"
    )

    result = (
        consensus.verify_node_bundle(
            "NODE-A",
            bundle,
        )
    )

    assert result["verified"] is True
    assert result["chain_tip"] is not None


def test_unauthorized_node_can_have_valid_bundle_but_is_excluded_by_authorization():
    """
    Чухал ялгаа:

    Bundle криптографийн хувьд хүчинтэй байж болно.
    Гэхдээ node authorization-д байхгүй бол
    V83 authorization түвшинд зөвшөөрөгдөхгүй.
    """

    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    unauthorized_bundle = build_bundle(
        "NODE-X"
    )

    consensus = MultiNodeConsensus(
        quorum=1
    )

    crypto_result = (
        consensus.verify_node_bundle(
            "NODE-X",
            unauthorized_bundle,
        )
    )

    assert crypto_result["verified"] is True

    assert not registry.is_authorized(
        "NODE-X"
    )


def test_authorized_two_of_three_nodes_reach_quorum():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
            "NODE-C",
        ]
    )

    bundle = build_bundle(
        "NODE-A"
    )

    consensus = MultiNodeConsensus(
        quorum=2
    )

    node_bundles = {
        "NODE-A": copy.deepcopy(bundle),
        "NODE-B": copy.deepcopy(bundle),
    }

    for node_id in node_bundles:
        assert registry.is_authorized(
            node_id
        )

    report = consensus.verify_network(
        node_bundles
    )

    assert (
        report["verified_node_count"]
        == 2
    )

    assert (
        report["consensus"]
        == "QUORUM_REACHED"
    )

    assert (
        report["consensus_count"]
        == 2
    )

    assert sorted(
        report["consensus_nodes"]
    ) == [
        "NODE-A",
        "NODE-B",
    ]


def test_unauthorized_node_does_not_count_toward_authorized_quorum():
    """
    NODE-A + NODE-B authorized.
    NODE-X unauthorized.

    Бүгд ижил хүчинтэй bundle-тэй байсан ч
    authorization шүүлтүүрийн дараа NODE-X
    quorum-д тооцогдохгүй.
    """

    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    bundle = build_bundle(
        "NODE-A"
    )

    node_bundles = {
        "NODE-A": copy.deepcopy(bundle),
        "NODE-B": copy.deepcopy(bundle),
        "NODE-X": copy.deepcopy(bundle),
    }

    authorized_bundles = {
        node_id: node_bundles[node_id]
        for node_id in node_bundles
        if registry.is_authorized(node_id)
    }

    consensus = MultiNodeConsensus(
        quorum=2
    )

    report = consensus.verify_network(
        authorized_bundles
    )

    assert (
        sorted(
            authorized_bundles.keys()
        )
        == [
            "NODE-A",
            "NODE-B",
        ]
    )

    assert (
        report["node_count"]
        == 2
    )

    assert (
        report["verified_node_count"]
        == 2
    )

    assert (
        report["consensus"]
        == "QUORUM_REACHED"
    )

    assert (
        report["consensus_count"]
        == 2
    )


def test_unauthorized_node_is_removed_before_consensus():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
            "NODE-X",
        ]
    )

    registry.remove(
        "NODE-X"
    )

    assert not registry.is_authorized(
        "NODE-X"
    )

    bundle = build_bundle(
        "NODE-A"
    )

    node_bundles = {
        "NODE-A": copy.deepcopy(bundle),
        "NODE-B": copy.deepcopy(bundle),
        "NODE-X": copy.deepcopy(bundle),
    }

    authorized_bundles = {
        node_id: bundle
        for node_id, bundle
        in node_bundles.items()
        if registry.is_authorized(node_id)
    }

    assert sorted(
        authorized_bundles.keys()
    ) == [
        "NODE-A",
        "NODE-B",
    ]

    consensus = MultiNodeConsensus(
        quorum=2
    )

    report = consensus.verify_network(
        authorized_bundles
    )

    assert (
        report["consensus"]
        == "QUORUM_REACHED"
    )

    assert (
        report["consensus_count"]
        == 2
    )


def test_authorization_does_not_replace_cryptographic_verification():
    """
    Authorized node байсан ч bundle эвдэрсэн бол
    cryptographic verification FAIL байна.
    """

    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    bundle = build_bundle(
        "NODE-A"
    )

    tampered = copy.deepcopy(
        bundle
    )

    tampered[
        "manifest_hash"
    ] = "0" * 64

    assert registry.is_authorized(
        "NODE-A"
    )

    consensus = MultiNodeConsensus(
        quorum=1
    )

    result = (
        consensus.verify_node_bundle(
            "NODE-A",
            tampered,
        )
    )

    assert result["verified"] is False
    assert result["chain_tip"] is None


def test_valid_crypto_does_not_replace_authorization():
    """
    Cryptographically valid bundle байгаа ч
    unauthorized node бол consensus-д оруулахгүй.
    """

    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    bundle = build_bundle(
        "NODE-X"
    )

    consensus = MultiNodeConsensus(
        quorum=1
    )

    crypto_result = (
        consensus.verify_node_bundle(
            "NODE-X",
            bundle,
        )
    )

    assert crypto_result["verified"] is True

    assert not registry.is_authorized(
        "NODE-X"
    )


def test_authorized_and_cryptographically_valid_node_passes_both_layers():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    bundle = build_bundle(
        "NODE-A"
    )

    consensus = MultiNodeConsensus(
        quorum=1
    )

    authorization_result = (
        registry.verify_node(
            "NODE-A"
        )
    )

    crypto_result = (
        consensus.verify_node_bundle(
            "NODE-A",
            bundle,
        )
    )

    assert (
        authorization_result["authorized"]
        is True
    )

    assert (
        crypto_result["verified"]
        is True
    )

    assert (
        crypto_result["chain_tip"]
        is not None
    )


def test_authorization_filter_preserves_chain_tip():
    """
    Authorization filter нь хүчинтэй bundle-ийн
    криптографийн Chain Tip-ийг өөрчлөхгүй.
    """

    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    bundle = build_bundle(
        "NODE-A"
    )

    consensus = MultiNodeConsensus(
        quorum=1
    )

    original_tip = (
        consensus.compute_chain_tip(
            bundle
        )
    )

    assert original_tip is not None

    authorized_bundles = {
        "NODE-A": copy.deepcopy(bundle),
    }

    report = consensus.verify_network(
        authorized_bundles
    )

    assert (
        report["chain_tip"]
        == original_tip
    )


def test_different_chain_tip_still_causes_split_consensus_after_authorization():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
            "NODE-C",
        ]
    )

    bundle_a = build_bundle(
        "NODE-A",
        buyer_balance=1000,
    )

    bundle_b = build_bundle(
        "NODE-B",
        buyer_balance=900,
    )

    bundle_c = build_bundle(
        "NODE-C",
        buyer_balance=800,
    )

    node_bundles = {
        "NODE-A": bundle_a,
        "NODE-B": bundle_b,
        "NODE-C": bundle_c,
    }

    authorized_bundles = {
        node_id: bundle
        for node_id, bundle
        in node_bundles.items()
        if registry.is_authorized(node_id)
    }

    consensus = MultiNodeConsensus(
        quorum=2
    )

    report = consensus.verify_network(
        authorized_bundles
    )

    assert (
        report["verified_node_count"]
        == 3
    )

    assert (
        report["consensus"]
        == "SPLIT_CONSENSUS"
    )

    assert (
        report["chain_tip"]
        is None
    )


def test_authorization_results_are_deterministic():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-C",
            "NODE-A",
            "NODE-B",
        ]
    )

    result_a = registry.verify_nodes(
        [
            "NODE-C",
            "NODE-A",
            "NODE-B",
            "NODE-X",
        ]
    )

    result_b = registry.verify_nodes(
        [
            "NODE-X",
            "NODE-B",
            "NODE-A",
            "NODE-C",
        ]
    )

    assert (
        result_a["authorized_nodes"]
        == result_b["authorized_nodes"]
    )

    assert (
        result_a["unauthorized_nodes"]
        == result_b["unauthorized_nodes"]
    )

    assert (
        result_a["results"]
        == result_b["results"]
    )


def test_authorization_registry_and_consensus_have_separate_responsibilities():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    bundle = build_bundle(
        "NODE-A"
    )

    consensus = MultiNodeConsensus(
        quorum=1
    )

    authorization = registry.is_authorized(
        "NODE-A"
    )

    cryptographic = (
        consensus.verify_node_bundle(
            "NODE-A",
            bundle,
        )
    )

    assert authorization is True
    assert cryptographic["verified"] is True

    assert (
        authorization
        and cryptographic["verified"]
    )


def test_revoked_node_fails_authorization_even_with_same_valid_bundle():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    bundle = build_bundle(
        "NODE-A"
    )

    consensus = MultiNodeConsensus(
        quorum=1
    )

    before = (
        consensus.verify_node_bundle(
            "NODE-A",
            bundle,
        )
    )

    assert before["verified"] is True
    assert registry.is_authorized(
        "NODE-A"
    )

    registry.remove(
        "NODE-A"
    )

    after = (
        consensus.verify_node_bundle(
            "NODE-A",
            bundle,
        )
    )

    assert after["verified"] is True
    assert not registry.is_authorized(
        "NODE-A"
    )


def test_authorized_quorum_requires_authorized_nodes_only():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    bundle = build_bundle(
        "NODE-A"
    )

    node_bundles = {
        "NODE-A": copy.deepcopy(bundle),
        "NODE-B": copy.deepcopy(bundle),
        "NODE-X": copy.deepcopy(bundle),
        "NODE-Y": copy.deepcopy(bundle),
    }

    authorized_bundles = {
        node_id: bundle
        for node_id, bundle
        in node_bundles.items()
        if registry.is_authorized(node_id)
    }

    assert sorted(
        authorized_bundles.keys()
    ) == [
        "NODE-A",
        "NODE-B",
    ]

    consensus = MultiNodeConsensus(
        quorum=2
    )

    report = consensus.verify_network(
        authorized_bundles
    )

    assert (
        report["node_count"]
        == 2
    )

    assert (
        report["consensus"]
        == "QUORUM_REACHED"
    )

    assert (
        report["consensus_count"]
        == 2
    )