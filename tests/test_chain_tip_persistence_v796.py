"""
GerChain V79.6
Chain Tip Persistence / Reload Integrity Tests.

Purpose:
- Canonical CHAIN_TIP-ийг сериалчилсны дараа хадгалах.
- Дахин уншсан өгөгдлөөс CHAIN_TIP-ийг бие даан дахин тооцоолох.
- Хадгалалт / сэргээх үйлдэл Chain Tip-ийг өөрчлөхгүй байхыг батлах.
- Дискэнд хадгалсан өгөгдөл өөрчлөгдвөл verifier татгалзахыг батлах.
"""

import copy
import json

from persistence.serializer import serialize_chain
from witness.chain import WitnessChain
from witness.independent_multi import (
    IndependentMultiWitnessEngine,
)


def create_chain(witness_id):
    initial_state = {
        "initialized": False,
        "sequence_counter": 0,
    }

    manifest = {
        "project": "V79.6-Chain-Tip-Persistence",
        "version": "1",
    }

    chain = WitnessChain(
        initial_state=initial_state,
        manifest=manifest,
        witness_id=witness_id,
    )

    chain.append_event(
        event_id="EVENT-001",
        event_type="TEST_EVENT",
        timestamp="2026-09-03T14:20:00Z",
        payload={
            "value": 100,
            "action": "first",
        },
        evidence={
            "document": "evidence-001",
        },
    )

    chain.append_event(
        event_id="EVENT-002",
        event_type="TEST_EVENT",
        timestamp="2026-09-03T14:21:00Z",
        payload={
            "value": 200,
            "action": "final",
        },
        evidence={
            "document": "evidence-002",
        },
    )

    return chain


def create_engine():
    return IndependentMultiWitnessEngine(
        quorum=2,
        authorized_witness_ids={
            "witness-1",
            "witness-2",
        },
    )


def decode_serialized(data):
    return json.loads(
        data.decode("utf-8")
    )


def test_chain_tip_survives_serialize_reload_round_trip():
    """
    Сериалчилсан өгөгдлийг дахин уншихад
    CHAIN_TIP өөрчлөгдөх ёсгүй.
    """

    chain = create_chain("witness-1")
    engine = create_engine()

    serialized = serialize_chain(chain)

    original_bundle = decode_serialized(
        serialized
    )

    assert engine.verifier.verify_bundle(
        original_bundle
    )

    original_tip = engine.compute_chain_tip(
        original_bundle
    )

    reloaded_bundle = decode_serialized(
        serialized
    )

    assert engine.verifier.verify_bundle(
        reloaded_bundle
    )

    reloaded_tip = engine.compute_chain_tip(
        reloaded_bundle
    )

    assert original_tip == reloaded_tip
    assert original_tip is not None
    assert len(original_tip) == 64


def test_reloaded_bundle_reaches_same_consensus():
    """
    Дахин уншсан ижил bundle нь өмнөхтэй адил
    зөвшилцөлд хүрэх ёстой.
    """

    chain_1 = create_chain("witness-1")
    chain_2 = create_chain("witness-2")

    engine = create_engine()

    bundle_1 = decode_serialized(
        serialize_chain(chain_1)
    )

    bundle_2 = decode_serialized(
        serialize_chain(chain_2)
    )

    result = engine.evaluate(
        [
            json.dumps(
                bundle_1,
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8"),
            json.dumps(
                bundle_2,
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8"),
        ]
    )

    assert result.status == "CONSENSUS"
    assert result.votes == 2
    assert result.consensus_hash is not None
    assert len(result.consensus_hash) == 64


def test_reloaded_tampered_bundle_is_rejected():
    """
    Reload хийсний дараа bundle-ийн түүхийг өөрчилбөл
    бие даасан verifier татгалзах ёстой.
    """

    chain = create_chain("witness-1")
    engine = create_engine()

    serialized = serialize_chain(chain)

    reloaded_bundle = decode_serialized(
        serialized
    )

    assert engine.verifier.verify_bundle(
        reloaded_bundle
    )

    tampered_bundle = copy.deepcopy(
        reloaded_bundle
    )

    tampered_bundle["entries"][0][
        "event_payload"
    ]["value"] = 999999

    assert not engine.verifier.verify_bundle(
        tampered_bundle
    )

    assert engine.compute_chain_tip(
        tampered_bundle
    ) is None