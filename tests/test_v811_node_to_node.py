"""
GerChain V81.1
Independent Node-to-Node Verification Tests.

Purpose:
- Node A-аас Node B рүү bundle дамжуулах.
- Node B bundle-ийг өөрөө бие даан шалгах.
- Зөв bundle-ийг ACCEPT хийх.
- Өөрчилсөн bundle-ийг REJECT хийх.
- Node A-ийн verification result-д найдахгүй байх.
"""

import json

from core.hashing import domain_hash
from network.node import WitnessNode
from persistence.serializer import serialize_chain
from witness.chain import WitnessChain


def build_chain():

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
            "version": "V81.1",
            "purpose": "Node-to-Node Verification",
        },
        witness_id="NODE-A-WITNESS-001",
        initial_money_state=money_state,
    )

    state_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        money_state,
    )

    chain.append_event(
        event_id="V811-INITIAL-MONEY-001",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T12:00:01",
        payload={
            "state": money_state,
            "state_hash": state_hash,
        },
        evidence={
            "type": "INITIAL_MONEY_COMMITMENT",
            "reference": "V811-001",
        },
    )

    return chain


def make_bundle():

    chain = build_chain()

    serialized = serialize_chain(
        chain
    )

    return json.loads(
        serialized.decode("utf-8")
    )


def recompute_event_hash(entry):

    record = entry["record"]

    event_obj = {
        "sequence": record["sequence"],
        "event_id": record["event_id"],
        "event_type": record["event_type"],
        "timestamp": record["timestamp"],
        "payload": entry["event_payload"],
    }

    return domain_hash(
        "WITNESS_EVENT",
        event_obj,
    )


def test_node_to_node_valid_bundle():

    bundle = make_bundle()

    node_a = WitnessNode(
        "NODE-A"
    )

    node_b = WitnessNode(
        "NODE-B"
    )

    assert (
        node_a.receive_bundle(bundle)
        is True
    )

    assert (
        node_b.receive_bundle(bundle)
        is True
    )

    assert (
        node_a.accepted_count()
        == 1
    )

    assert (
        node_b.accepted_count()
        == 1
    )


def test_node_b_rejects_tampered_balance():

    bundle = make_bundle()

    node_a = WitnessNode(
        "NODE-A"
    )

    node_b = WitnessNode(
        "NODE-B"
    )

    assert (
        node_a.receive_bundle(bundle)
        is True
    )

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
    ] = 900

    assert (
        node_b.receive_bundle(bundle)
        is False
    )

    assert (
        node_b.accepted_count()
        == 0
    )

    assert (
        node_b.rejected_count_total()
        == 1
    )


def test_node_b_rejects_tampered_bundle_with_recomputed_event_hash():

    bundle = make_bundle()

    node_a = WitnessNode(
        "NODE-A"
    )

    node_b = WitnessNode(
        "NODE-B"
    )

    assert (
        node_a.receive_bundle(bundle)
        is True
    )

    entry = bundle[
        "entries"
    ][0]

    entry[
        "event_payload"
    ][
        "state"
    ][
        "currency"
    ] = "USD"

    entry[
        "record"
    ][
        "event_hash"
    ] = recompute_event_hash(
        entry
    )

    assert (
        node_b.receive_bundle(bundle)
        is False
    )


def test_node_b_does_not_trust_node_a_result():

    bundle = make_bundle()

    node_a = WitnessNode(
        "NODE-A"
    )

    node_b = WitnessNode(
        "NODE-B"
    )

    node_a_result = (
        node_a.receive_bundle(
            bundle
        )
    )

    assert node_a_result is True

    # Node A-ийн PASS үр дүнг дамжуулахгүй.
    # Node B өөрөө bundle-ийг дахин шалгана.

    assert (
        node_b.receive_bundle(
            bundle
        )
        is True
    )

    assert (
        node_b.accepted_count()
        == 1
    )


def test_node_b_has_independent_verifier():

    node_a = WitnessNode(
        "NODE-A"
    )

    node_b = WitnessNode(
        "NODE-B"
    )

    assert (
        node_a.verifier
        is not node_b.verifier
    )


def test_node_b_rejects_tampered_initial_state_hash():

    bundle = make_bundle()

    node_a = WitnessNode(
        "NODE-A"
    )

    node_b = WitnessNode(
        "NODE-B"
    )

    assert (
        node_a.receive_bundle(bundle)
        is True
    )

    entry = bundle[
        "entries"
    ][0]

    entry[
        "event_payload"
    ][
        "state_hash"
    ] = "0" * 64

    entry[
        "record"
    ][
        "event_hash"
    ] = recompute_event_hash(
        entry
    )

    assert (
        node_b.receive_bundle(bundle)
        is False
    )

    assert (
        node_b.accepted_count()
        == 0
    )


def test_node_b_accepts_unchanged_bundle_after_node_a():

    bundle = make_bundle()

    node_a = WitnessNode(
        "NODE-A"
    )

    node_b = WitnessNode(
        "NODE-B"
    )

    assert (
        node_a.receive_bundle(bundle)
        is True
    )

    assert (
        node_b.receive_bundle(bundle)
        is True
    )

    assert (
        node_a.rejected_count_total()
        == 0
    )

    assert (
        node_b.rejected_count_total()
        == 0
    )