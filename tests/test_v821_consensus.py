"""
GerChain V82.1
Multi-Node Cryptographic Consensus Tests.

Purpose:
- Ижил bundle-тай олон node ижил Chain Tip гаргах.
- Quorum зөв тогтоох.
- Өөр Chain Tip-үүдийг салгаж таних.
- Буруу bundle-ийг consensus-д оруулахгүй байх.
- Chain Tip-ийг эх өгөгдлөөс дахин тооцох.
- Manifest hash болон event hash-ийн integrity-г шалгах.
- V79.3 recursive State Root-ийг ашиглах.
"""

from __future__ import annotations

import copy
import json

from core.hashing import domain_hash
from network.consensus import MultiNodeConsensus
from witness.chain import WitnessChain
from persistence.serializer import serialize_chain


def build_bundle(
    witness_id: str,
    buyer_balance: int = 1000,
):
    """
    Туршилтын хүчинтэй Witness Bundle үүсгэнэ.
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
            "version": "V82.1",
            "purpose": "Cryptographic Consensus",
        },
        witness_id=witness_id,
        initial_money_state=money_state,
    )

    state_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        money_state,
    )

    chain.append_event(
        event_id="V821-INITIAL-MONEY-001",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T15:00:01",
        payload={
            "state": money_state,
            "state_hash": state_hash,
        },
        evidence={
            "type": "INITIAL_MONEY_COMMITMENT",
            "reference": "V821-001",
        },
    )

    return json.loads(
        serialize_chain(
            chain
        ).decode("utf-8")
    )


def test_same_bundle_produces_same_chain_tip():
    bundle = build_bundle(
        "NODE-A"
    )

    consensus = MultiNodeConsensus(
        quorum=2
    )

    tip_a = consensus.compute_chain_tip(
        bundle
    )

    tip_b = consensus.compute_chain_tip(
        copy.deepcopy(bundle)
    )

    assert tip_a is not None
    assert tip_a == tip_b


def test_three_identical_nodes_reach_quorum():
    bundle = build_bundle(
        "NODE-A"
    )

    node_bundles = {
        "NODE-A": copy.deepcopy(bundle),
        "NODE-B": copy.deepcopy(bundle),
        "NODE-C": copy.deepcopy(bundle),
    }

    consensus = MultiNodeConsensus(
        quorum=2
    )

    report = consensus.verify_network(
        node_bundles
    )

    assert (
        report["verified_node_count"]
        == 3
    )

    assert (
        report["consensus"]
        == "QUORUM_REACHED"
    )

    assert (
        report["consensus_count"]
        == 3
    )

    assert sorted(
        report["consensus_nodes"]
    ) == [
        "NODE-A",
        "NODE-B",
        "NODE-C",
    ]

    assert (
        report["chain_tip"]
        is not None
    )


def test_two_of_three_nodes_reach_quorum():
    """
    3 node байна.

    NODE-A + NODE-B:
        ижил Chain Tip.

    NODE-C:
        өөр Chain Tip.

    Quorum = 2 тул
    зөвшилцөл NODE-A + NODE-B дээр тогтоно.
    """

    bundle = build_bundle(
        "NODE-A"
    )

    different_bundle = build_bundle(
        "NODE-C",
        buyer_balance=900,
    )

    node_bundles = {
        "NODE-A": copy.deepcopy(bundle),
        "NODE-B": copy.deepcopy(bundle),
        "NODE-C": different_bundle,
    }

    consensus = MultiNodeConsensus(
        quorum=2
    )

    report = consensus.verify_network(
        node_bundles
    )

    assert (
        report["verified_node_count"]
        == 3
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

    assert (
        report["chain_tip"]
        == consensus.compute_chain_tip(
            bundle
        )
    )


def test_different_money_state_produces_different_chain_tip():
    """
    initial_money_state өөрчлөгдвөл
    Chain Tip өөрчлөгдөж байгааг шалгана.
    """

    bundle_a = build_bundle(
        "NODE-A",
        buyer_balance=1000,
    )

    bundle_b = build_bundle(
        "NODE-B",
        buyer_balance=900,
    )

    consensus = MultiNodeConsensus(
        quorum=1
    )

    tip_a = consensus.compute_chain_tip(
        bundle_a
    )

    tip_b = consensus.compute_chain_tip(
        bundle_b
    )

    assert tip_a is not None
    assert tip_b is not None

    assert tip_a != tip_b


def test_split_chain_tips_do_not_reach_quorum():
    """
    3 өөр хүчинтэй Chain Tip байна.

    Quorum = 2.

    Аль ч Chain Tip 2 node-д хүрээгүй тул
    SPLIT_CONSENSUS болно.
    """

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

    consensus = MultiNodeConsensus(
        quorum=2
    )

    report = consensus.verify_network(
        {
            "NODE-A": bundle_a,
            "NODE-B": bundle_b,
            "NODE-C": bundle_c,
        }
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

    assert (
        report["consensus_count"]
        == 0
    )


def test_tampered_bundle_is_not_verified():
    """
    Payload өөрчлөгдсөн боловч event_hash
    өөрчлөгдөөгүй тул bundle REJECT болно.
    """

    bundle = build_bundle(
        "NODE-A"
    )

    tampered = copy.deepcopy(
        bundle
    )

    tampered[
        "entries"
    ][0][
        "event_payload"
    ][
        "state"
    ][
        "balances"
    ][
        "BUYER"
    ] = 500

    consensus = MultiNodeConsensus(
        quorum=1
    )

    result = (
        consensus.verify_node_bundle(
            "NODE-TAMPER",
            tampered,
        )
    )

    assert (
        result["verified"]
        is False
    )

    assert (
        result["chain_tip"]
        is None
    )


def test_recomputed_event_hash_creates_valid_new_history():
    """
    Payload өөрчлөгдөж,
    event_hash мөн зөв дахин тооцогдсон бол
    криптографийн хувьд шинэ хүчинтэй history
    байж болно.

    Тиймээс verifier үүнийг REJECT хийх ёсгүй.
    """

    bundle = build_bundle(
        "NODE-A"
    )

    modified = copy.deepcopy(
        bundle
    )

    entry = modified[
        "entries"
    ][0]

    entry[
        "event_payload"
    ][
        "state"
    ][
        "currency"
    ] = "USD"

    record = entry[
        "record"
    ]

    event_obj = {
        "sequence": record[
            "sequence"
        ],
        "event_id": record[
            "event_id"
        ],
        "event_type": record[
            "event_type"
        ],
        "timestamp": record[
            "timestamp"
        ],
        "payload": entry[
            "event_payload"
        ],
    }

    record[
        "event_hash"
    ] = domain_hash(
        "WITNESS_EVENT",
        event_obj,
    )

    consensus = MultiNodeConsensus(
        quorum=1
    )

    result = (
        consensus.verify_node_bundle(
            "NODE-MODIFIED",
            modified,
        )
    )

    assert (
        result["verified"]
        is True
    )

    assert (
        result["chain_tip"]
        is not None
    )


def test_chain_tip_changes_when_actual_state_changes():
    """
    Event payload дахь state өөрчлөгдөхөд
    event hash → state hash → state root →
    Chain Tip гэсэн бүх холбоос шинэчлэгдэнэ.
    """

    bundle_a = build_bundle(
        "NODE-A",
        buyer_balance=1000,
    )

    bundle_b = build_bundle(
        "NODE-B",
        buyer_balance=900,
    )

    consensus = MultiNodeConsensus(
        quorum=1
    )

    result_a = (
        consensus.verify_node_bundle(
            "NODE-A",
            bundle_a,
        )
    )

    result_b = (
        consensus.verify_node_bundle(
            "NODE-B",
            bundle_b,
        )
    )

    assert (
        result_a["verified"]
        is True
    )

    assert (
        result_b["verified"]
        is True
    )

    assert (
        result_a["chain_tip"]
        is not None
    )

    assert (
        result_b["chain_tip"]
        is not None
    )

    assert (
        result_a["chain_tip"]
        != result_b["chain_tip"]
    )


def test_invalid_bundle_is_excluded_from_consensus():
    valid_bundle = build_bundle(
        "NODE-A"
    )

    invalid_bundle = copy.deepcopy(
        valid_bundle
    )

    invalid_bundle[
        "entries"
    ][0][
        "event_payload"
    ][
        "state_hash"
    ] = "0" * 64

    consensus = MultiNodeConsensus(
        quorum=2
    )

    report = consensus.verify_network(
        {
            "NODE-A": valid_bundle,
            "NODE-B": valid_bundle,
            "NODE-C": invalid_bundle,
        }
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


def test_quorum_not_reached_with_two_different_valid_nodes():
    """
    2 өөр Chain Tip,
    quorum = 2.

    Аль ч Chain Tip 2 node-д байхгүй.
    """

    bundle_a = build_bundle(
        "NODE-A"
    )

    bundle_b = build_bundle(
        "NODE-B",
        buyer_balance=900,
    )

    consensus = MultiNodeConsensus(
        quorum=2
    )

    report = consensus.verify_network(
        {
            "NODE-A": bundle_a,
            "NODE-B": bundle_b,
        }
    )

    assert (
        report["verified_node_count"]
        == 2
    )

    assert (
        report["consensus"]
        == "SPLIT_CONSENSUS"
    )

    assert (
        report["chain_tip"]
        is None
    )


def test_empty_network_has_no_valid_nodes():
    consensus = MultiNodeConsensus(
        quorum=2
    )

    report = consensus.verify_network(
        {}
    )

    assert (
        report["node_count"]
        == 0
    )

    assert (
        report["verified_node_count"]
        == 0
    )

    assert (
        report["consensus"]
        == "NO_VALID_NODES"
    )

    assert (
        report["chain_tip"]
        is None
    )


def test_node_results_are_independent():
    bundle = build_bundle(
        "NODE-A"
    )

    consensus = MultiNodeConsensus(
        quorum=2
    )

    result_a = (
        consensus.verify_node_bundle(
            "NODE-A",
            copy.deepcopy(bundle),
        )
    )

    result_b = (
        consensus.verify_node_bundle(
            "NODE-B",
            copy.deepcopy(bundle),
        )
    )

    assert (
        result_a["verified"]
        is True
    )

    assert (
        result_b["verified"]
        is True
    )

    assert (
        result_a["chain_tip"]
        == result_b["chain_tip"]
    )

    assert (
        result_a["node_id"]
        != result_b["node_id"]
    )


def test_stored_manifest_hash_tampering_is_rejected():
    """
    Stored manifest_hash өөрчлөгдвөл
    IndependentVerifier REJECT хийнэ.
    """

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

    tampered = copy.deepcopy(
        bundle
    )

    tampered[
        "manifest_hash"
    ] = "0" * 64

    recomputed_tip = (
        consensus.compute_chain_tip(
            tampered
        )
    )

    assert (
        recomputed_tip
        is None
    )


def test_stored_chain_tip_is_not_used():
    """
    Bundle дотор хуурамч chain_tip нэмсэн ч
    consensus engine түүнд итгэхгүй.

    Chain Tip-ийг manifest + state history-оос
    дахин тооцно.
    """

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

    tampered = copy.deepcopy(
        bundle
    )

    tampered[
        "chain_tip"
    ] = "0" * 64

    recomputed_tip = (
        consensus.compute_chain_tip(
            tampered
        )
    )

    assert (
        recomputed_tip
        == original_tip
    )


def test_chain_tip_contains_recursive_state_root():
    """
    V79.3 recursive State Root нь
    V82.1 Chain Tip-ийн бүрэлдэхүүнд
    орж байгааг шалгана.
    """

    bundle = build_bundle(
        "NODE-A"
    )

    consensus = MultiNodeConsensus(
        quorum=1
    )

    state_root = (
        consensus.verifier.compute_state_root(
            bundle
        )
    )

    chain_tip = (
        consensus.compute_chain_tip(
            bundle
        )
    )

    assert state_root is not None
    assert chain_tip is not None

    expected_manifest_hash = (
        domain_hash(
            "MANIFEST",
            bundle["manifest"],
        )
    )

    record = bundle[
        "entries"
    ][-1][
        "record"
    ]

    expected = domain_hash(
        "CHAIN_TIP",
        {
            "manifest_hash":
                expected_manifest_hash,
            "final_sequence":
                record["sequence"],
            "final_state_hash":
                record["new_state_hash"],
            "state_root":
                state_root,
        },
    )

    assert (
        chain_tip
        == expected
    )