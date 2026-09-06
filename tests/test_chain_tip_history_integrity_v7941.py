"""
GerChain V79.4.1
Chain Tip History Integrity Tests.

Purpose:
- Гинжийн өмнөх түүх өөрчлөгдөхөд STATE_ROOT өөрчлөгдөхийг батлах.
- Ижил төгсгөлийн төлөв харагдсан ч өмнөх түүх өөр бол
  Chain Tip ижил хэвээр үлдэхгүй байхыг батлах.
- Stored hash-д сохроор итгэхгүй, бүх түүхийг дахин тооцоолдог
  V79.3/V79.4 хамгаалалтыг батлах.
"""

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
        "project": "V79.4.1-Chain-Tip-History-Integrity",
        "version": "1",
    }

    return WitnessChain(
        initial_state=initial_state,
        manifest=manifest,
        witness_id=witness_id,
    )


def append_event(
    chain,
    event_id,
    value,
    action,
    timestamp,
):
    chain.append_event(
        event_id=event_id,
        event_type="TEST_EVENT",
        timestamp=timestamp,
        payload={
            "value": value,
            "action": action,
        },
        evidence={
            "document": f"evidence-{event_id}",
        },
    )


def create_engine():
    return IndependentMultiWitnessEngine(
        quorum=2,
        authorized_witness_ids={
            "witness-1",
            "witness-2",
        },
    )


def test_modified_history_changes_chain_tip():
    """
    Эхний үйл явдлын түүх өөрчлөгдвөл эцсийн Chain Tip
    өөрчлөгдөх ёстой.

    Witness-1 болон Witness-2 эхэндээ ижил түүхтэй.
    Дараа нь Witness-2-ийн эхний event payload-ийг
    өөрчилнө.

    Stored event_hash болон state hash-уудыг дахин тооцоолохгүй.
    Иймээс бие даасан баталгаажуулагч өөрчлөлтийг илрүүлэх ёстой.
    """

    chain_1 = create_chain("witness-1")
    chain_2 = create_chain("witness-2")

    for chain in [chain_1, chain_2]:
        append_event(
            chain=chain,
            event_id="EVENT-001",
            value=100,
            action="first",
            timestamp="2026-09-03T13:20:00Z",
        )

        append_event(
            chain=chain,
            event_id="EVENT-002",
            value=200,
            action="final",
            timestamp="2026-09-03T13:21:00Z",
        )

    bundle_1 = serialize_chain(chain_1)
    bundle_2 = serialize_chain(chain_2)

    engine = create_engine()

    original_root_1 = engine.verifier.compute_state_root(
        json.loads(bundle_1.decode("utf-8"))
    )

    original_root_2 = engine.verifier.compute_state_root(
        json.loads(bundle_2.decode("utf-8"))
    )

    assert original_root_1 == original_root_2

    tampered = json.loads(
        bundle_2.decode("utf-8")
    )

    tampered["entries"][0]["event_payload"]["value"] = 999

    tampered_bundle = json.dumps(
        tampered,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    tampered_root = engine.verifier.compute_state_root(
        tampered
    )

    assert tampered_root is None


def test_same_final_state_different_history_must_not_share_chain_tip():
    """
    Өмнөх түүх өөр боловч эцсийн төлөв ижил болсон тохиолдолд
    Chain Tip-ийг ижил гэж үзэж болохгүй.

    Энэ нь зөвхөн final_state дээр consensus байгуулах
    боломжит алдааг хаана.
    """

    chain_1 = create_chain("witness-1")
    chain_2 = create_chain("witness-2")

    append_event(
        chain=chain_1,
        event_id="EVENT-001",
        value=100,
        action="history-a",
        timestamp="2026-09-03T13:20:00Z",
    )

    append_event(
        chain=chain_2,
        event_id="EVENT-001",
        value=999,
        action="history-b",
        timestamp="2026-09-03T13:20:00Z",
    )

    append_event(
        chain=chain_1,
        event_id="EVENT-002",
        value=200,
        action="final",
        timestamp="2026-09-03T13:21:00Z",
    )

    append_event(
        chain=chain_2,
        event_id="EVENT-002",
        value=200,
        action="final",
        timestamp="2026-09-03T13:21:00Z",
    )

    bundle_1 = serialize_chain(chain_1)
    bundle_2 = serialize_chain(chain_2)

    engine = create_engine()

    result = engine.evaluate(
        [
            bundle_1,
            bundle_2,
        ]
    )

    assert result.status == "REJECTED"
    assert result.votes == 1
    assert result.consensus_hash is None
    assert result.dissenting_witness_ids == [
        "witness-2",
    ]