"""
GerChain V82.0
Multi-Node Witness Network Tests.

Purpose:
- Олон Witness Node үүсгэх.
- Нэг bundle-ийг олон node-д дамжуулах.
- Node бүр бие даан verification хийх.
- Зөв bundle дээр quorum хүрэх.
- Буруу bundle дээр бүх node REJECT хийх.
- Нэг node-ийн PASS бусад node-д автоматаар
  нөлөөлөхгүйг шалгах.
"""

from __future__ import annotations

import json

from core.hashing import domain_hash
from network.multi_node import MultiNodeNetwork
from network.node import WitnessNode
from persistence.serializer import serialize_chain
from witness.chain import WitnessChain


def build_bundle():

    money_state = {
        "currency": "MNT",
        "balances": {
            "BUYER": 1000,
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
            "version": "V82.0",
            "purpose": "Multi-Node Witness Network",
        },
        witness_id="NODE-A-V820",
        initial_money_state=money_state,
    )

    state_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        money_state,
    )

    chain.append_event(
        event_id="V820-INITIAL-MONEY-001",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T14:00:01",
        payload={
            "state": money_state,
            "state_hash": state_hash,
        },
        evidence={
            "type": "INITIAL_MONEY_COMMITMENT",
            "reference": "V820-001",
        },
    )

    return json.loads(
        serialize_chain(chain).decode("utf-8")
    )


def build_network(
    quorum=2,
):

    network = MultiNodeNetwork(
        quorum=quorum
    )

    network.add_node(
        WitnessNode("NODE-A")
    )

    network.add_node(
        WitnessNode("NODE-B")
    )

    network.add_node(
        WitnessNode("NODE-C")
    )

    return network


def test_three_nodes_are_registered():

    network = build_network()

    assert (
        network.node_count()
        == 3
    )

    assert sorted(
        network.nodes.keys()
    ) == [
        "NODE-A",
        "NODE-B",
        "NODE-C",
    ]


def test_valid_bundle_is_accepted_by_all_nodes():

    network = build_network(
        quorum=2
    )

    bundle = build_bundle()

    report = network.verify_network(
        bundle
    )

    assert (
        report["accepted_count"]
        == 3
    )

    assert (
        report["rejected_count"]
        == 0
    )

    assert (
        report["consensus"]
        == "QUORUM_REACHED"
    )

    assert sorted(
        report["accepted_nodes"]
    ) == [
        "NODE-A",
        "NODE-B",
        "NODE-C",
    ]


def test_tampered_bundle_is_rejected_by_all_nodes():

    network = build_network(
        quorum=2
    )

    bundle = build_bundle()

    bundle[
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

    report = network.verify_network(
        bundle
    )

    assert (
        report["accepted_count"]
        == 0
    )

    assert (
        report["rejected_count"]
        == 3
    )

    assert (
        report["consensus"]
        == "QUORUM_NOT_REACHED"
    )

    assert report[
        "accepted_nodes"
    ] == []

    assert sorted(
        report["rejected_nodes"]
    ) == [
        "NODE-A",
        "NODE-B",
        "NODE-C",
    ]


def test_each_node_has_independent_verifier():

    network = build_network()

    node_a = network.nodes[
        "NODE-A"
    ]

    node_b = network.nodes[
        "NODE-B"
    ]

    node_c = network.nodes[
        "NODE-C"
    ]

    assert (
        node_a.verifier
        is not node_b.verifier
    )

    assert (
        node_a.verifier
        is not node_c.verifier
    )

    assert (
        node_b.verifier
        is not node_c.verifier
    )


def test_quorum_two_of_three_is_reached():

    network = build_network(
        quorum=2
    )

    results = {
        "NODE-A": True,
        "NODE-B": True,
        "NODE-C": False,
    }

    assert (
        network.accepted_count(
            results
        )
        == 2
    )

    assert (
        network.rejected_count(
            results
        )
        == 1
    )

    assert (
        network.has_quorum(
            results
        )
        is True
    )

    assert (
        network.consensus_result(
            results
        )
        == "QUORUM_REACHED"
    )


def test_quorum_two_of_three_is_not_reached():

    network = build_network(
        quorum=2
    )

    results = {
        "NODE-A": True,
        "NODE-B": False,
        "NODE-C": False,
    }

    assert (
        network.accepted_count(
            results
        )
        == 1
    )

    assert (
        network.rejected_count(
            results
        )
        == 2
    )

    assert (
        network.has_quorum(
            results
        )
        is False
    )

    assert (
        network.consensus_result(
            results
        )
        == "QUORUM_NOT_REACHED"
    )


def test_no_nodes_cannot_reach_quorum():

    network = MultiNodeNetwork(
        quorum=1
    )

    results = {}

    assert (
        network.accepted_count(
            results
        )
        == 0
    )

    assert (
        network.has_quorum(
            results
        )
        is False
    )

    assert (
        network.consensus_result(
            results
        )
        == "NO_NODES"
    )


def test_remove_node():

    network = build_network()

    assert (
        network.node_count()
        == 3
    )

    network.remove_node(
        "NODE-C"
    )

    assert (
        network.node_count()
        == 2
    )

    assert (
        "NODE-C"
        not in network.nodes
    )


def test_duplicate_node_is_rejected():

    network = build_network()

    try:
        network.add_node(
            WitnessNode("NODE-A")
        )
    except ValueError:
        return

    assert False, (
        "Duplicate node IDs "
        "must be rejected."
    )


def test_unknown_node_removal_is_rejected():

    network = build_network()

    try:
        network.remove_node(
            "NODE-UNKNOWN"
        )
    except ValueError:
        return

    assert False, (
        "Removing an unknown node "
        "must be rejected."
    )


def test_invalid_node_type_is_rejected():

    network = MultiNodeNetwork(
        quorum=1
    )

    try:
        network.add_node(
            "NOT-A-NODE"
        )
    except TypeError:
        return

    assert False, (
        "Only WitnessNode instances "
        "must be accepted."
    )


def test_network_status_is_deterministic():

    network = build_network(
        quorum=2
    )

    status = network.status()

    assert status == {
        "version": "V82.0",
        "node_count": 3,
        "quorum": 2,
        "node_ids": [
            "NODE-A",
            "NODE-B",
            "NODE-C",
        ],
        "verification_rounds": 0,
    }


def test_verification_round_is_recorded():

    network = build_network(
        quorum=2
    )

    bundle = build_bundle()

    report = network.verify_network(
        bundle
    )

    assert (
        report["consensus"]
        == "QUORUM_REACHED"
    )

    status = network.status()

    assert (
        status["verification_rounds"]
        == 1
    )


def test_quorum_three_requires_all_nodes():

    network = build_network(
        quorum=3
    )

    bundle = build_bundle()

    report = network.verify_network(
        bundle
    )

    assert (
        report["accepted_count"]
        == 3
    )

    assert (
        report["consensus"]
        == "QUORUM_REACHED"
    )