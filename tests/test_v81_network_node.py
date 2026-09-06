"""
GerChain V81.0
Witness Network Node Tests.

Purpose:
- WitnessNode зөв bundle хүлээн авах.
- Буруу bundle-г татгалзах.
- Tampered bundle-г хүлээн авахгүй байх.
- Serialized bundle-г бие даан шалгах.
- Node accepted/rejected төлвийг шалгах.
"""

import json

from persistence.serializer import serialize_chain
from verifier.v80_independent_verifier import (
    V80IndependentVerifier,
)
from witness.chain import WitnessChain
from network.node import WitnessNode


def build_valid_chain():

    chain = WitnessChain(
        initial_state={
            "value": 0,
            "sequence_counter": 0,
            "initialized": False,
        },
        manifest={
            "system": "GerChain",
            "version": "V81.0",
            "purpose": "Network Witness Node",
        },
        witness_id="WITNESS-NODE-001",
        initial_money_state={
            "currency": "MNT",
            "balances": {
                "BUYER": 1000,
                "SELLER": 0,
            },
        },
    )

    chain.append_event(
        event_id="INITIAL-MONEY-V81-001",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T10:00:01",
        payload={
            "state": {
                "currency": "MNT",
                "balances": {
                    "BUYER": 1000,
                    "SELLER": 0,
                },
            },
            "state_hash": (
                __import__(
                    "core.hashing",
                    fromlist=["domain_hash"],
                ).domain_hash(
                    "INITIAL_MONEY_STATE",
                    {
                        "currency": "MNT",
                        "balances": {
                            "BUYER": 1000,
                            "SELLER": 0,
                        },
                    },
                )
            ),
        },
        evidence={
            "type": "INITIAL_MONEY_COMMITMENT",
            "reference": "V81-INITIAL-001",
        },
    )

    return chain


def make_bundle():

    chain = build_valid_chain()

    serialized = serialize_chain(
        chain
    )

    return json.loads(
        serialized.decode("utf-8")
    )


def test_valid_bundle_is_accepted():

    bundle = make_bundle()

    node = WitnessNode(
        "NODE-V81-001"
    )

    assert (
        node.receive_bundle(bundle)
        is True
    )

    assert (
        node.accepted_count()
        == 1
    )

    assert (
        node.rejected_count_total()
        == 0
    )


def test_invalid_bundle_is_rejected():

    bundle = make_bundle()

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

    node = WitnessNode(
        "NODE-V81-002"
    )

    assert (
        node.receive_bundle(bundle)
        is False
    )

    assert (
        node.accepted_count()
        == 0
    )

    assert (
        node.rejected_count_total()
        == 1
    )


def test_tampered_bundle_with_recomputed_event_hash_is_rejected():

    bundle = make_bundle()

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

    from core.hashing import domain_hash

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

    node = WitnessNode(
        "NODE-V81-003"
    )

    assert (
        node.receive_bundle(bundle)
        is False
    )


def test_serialized_valid_bundle_is_accepted():

    chain = build_valid_chain()

    serialized = serialize_chain(
        chain
    )

    node = WitnessNode(
        "NODE-V81-004"
    )

    assert (
        node.receive_bytes(
            serialized
        )
        is True
    )

    assert (
        node.accepted_count()
        == 1
    )


def test_serialized_tampered_bundle_is_rejected():

    chain = build_valid_chain()

    serialized = serialize_chain(
        chain
    )

    bundle = json.loads(
        serialized.decode("utf-8")
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
    ] = 500

    tampered_bytes = json.dumps(
        bundle,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    node = WitnessNode(
        "NODE-V81-005"
    )

    assert (
        node.receive_bytes(
            tampered_bytes
        )
        is False
    )


def test_node_status_is_deterministic():

    node = WitnessNode(
        "NODE-V81-006"
    )

    status = node.status()

    assert status == {
        "version": "V81.0",
        "node_id": "NODE-V81-006",
        "accepted_bundles": 0,
        "rejected_bundles": 0,
    }