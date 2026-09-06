"""
GerChain V79.5
Canonical Chain Tip Tamper Tests.

Purpose:
- CHAIN_TIP-ийн үндсэн бүрэлдэхүүн бүр өөрчлөгдвөл
  эцсийн Chain Tip өөрчлөгдөхийг батлах.
- Хуурамчаар өөрчилсөн Chain Tip-ийг зөвшөөрөхгүй байх.
"""

import copy

from persistence.serializer import serialize_chain
from witness.chain import WitnessChain
from witness.independent_multi import (
    IndependentMultiWitnessEngine,
)


def create_chain():
    initial_state = {
        "initialized": False,
        "sequence_counter": 0,
    }

    manifest = {
        "project": "V79.5-Tamper-Test",
        "version": "1",
    }

    chain = WitnessChain(
        initial_state=initial_state,
        manifest=manifest,
        witness_id="witness-1",
    )

    chain.append_event(
        event_id="EVENT-001",
        event_type="TEST_EVENT",
        timestamp="2026-09-03T13:20:00Z",
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
        timestamp="2026-09-03T13:21:00Z",
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

def get_valid_bundle():
    chain = create_chain()
    engine = create_engine()

    bundle = engine._decode_bundle(
        serialize_chain(chain)
    )

    assert bundle is not None

    assert engine.verifier.verify_bundle(bundle)

    return engine, bundle


def test_manifest_hash_tamper_changes_chain_tip():
    engine, bundle = get_valid_bundle()

    original_tip = engine.compute_chain_tip(bundle)

    tampered = copy.deepcopy(bundle)
    tampered["manifest_hash"] = "0" * 64

    assert engine.compute_chain_tip(tampered) is None

    assert original_tip is not None


def test_final_sequence_tamper_changes_chain_tip():
    engine, bundle = get_valid_bundle()

    original_tip = engine.compute_chain_tip(bundle)

    recomputed = engine.verifier._recompute_bundle(bundle)

    assert recomputed is not None

    tampered = copy.deepcopy(bundle)

    tampered["entries"] = copy.deepcopy(
        bundle["entries"]
    )

    tampered["entries"][-1]["record"]["sequence"] = (
        recomputed["final_sequence"] + 1
    )

    assert engine.compute_chain_tip(tampered) is None

    assert original_tip is not None


def test_final_state_hash_tamper_changes_chain_tip():
    engine, bundle = get_valid_bundle()

    original_tip = engine.compute_chain_tip(bundle)

    tampered = copy.deepcopy(bundle)

    tampered["entries"][-1]["record"][
        "new_state_hash"
    ] = "0" * 64

    assert engine.compute_chain_tip(tampered) is None

    assert original_tip is not None


def test_state_root_tamper_changes_chain_tip():
    engine, bundle = get_valid_bundle()

    original_tip = engine.compute_chain_tip(bundle)

    recomputed = engine.verifier._recompute_bundle(bundle)

    assert recomputed is not None

    valid_root = recomputed["state_root"]

    tampered_root = "0" * 64

    assert tampered_root != valid_root

    tampered = copy.deepcopy(bundle)

    # STATE_ROOT нь bundle-д тусдаа хадгалагддаггүй.
    # Тиймээс ижил түүхээс өөр Chain Tip үүсгэх боломжгүйг
    # compute_chain_tip өөрөө баталгаажуулна.
    #
    # Хуурамч root-ийг CHAIN_TIP-д шууд оруулахад
    # canonical hash өөрчлөгдөнө.
    from core.hashing import domain_hash

    fake_tip = domain_hash(
        "CHAIN_TIP",
        {
            "manifest_hash": tampered["manifest_hash"],
            "final_sequence": recomputed["final_sequence"],
            "final_state_hash": recomputed["final_state_hash"],
            "state_root": tampered_root,
        },
    )

    assert fake_tip != original_tip

    # Харин бодит verifier зөв STATE_ROOT-ийг дахин тооцно.
    actual_tip = engine.compute_chain_tip(tampered)

    assert actual_tip == original_tip


def test_tampered_bundle_cannot_reach_consensus():
    engine, bundle = get_valid_bundle()

    valid_bundle = copy.deepcopy(bundle)

    tampered_bundle = copy.deepcopy(bundle)

    tampered_bundle["entries"][-1]["record"][
        "new_state_hash"
    ] = "0" * 64

    result = engine.evaluate(
        [
            serialize_bundle(valid_bundle),
            serialize_bundle(tampered_bundle),
        ]
    )

    assert result.status == "REJECTED"
    assert result.votes == 1
    assert result.consensus_hash is None
    assert result.valid_witness_ids == [
        "witness-1"
    ]


def serialize_bundle(bundle):
    import json

    return json.dumps(
        bundle,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")