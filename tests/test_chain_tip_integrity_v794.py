"""
GerChain V79.4
Chain Tip Integrity Tests.

Purpose:
- Олон гэрчийн manifest_hash нийцлийг шалгах.
- Өөр manifest-тэй гэрчийг ижил STATE_ROOT-той байсан ч
  ижил Chain Tip гэж үзэхгүй байх.
- Ижил manifest-тай гэрчүүд quorum бүрдүүлж чаддагийг батлах.
"""

from persistence.serializer import serialize_chain
from witness.chain import WitnessChain
from witness.independent_multi import (
    IndependentMultiWitnessEngine,
)


def create_chain(
    witness_id,
    manifest_version="1",
):
    initial_state = {
        "initialized": False,
        "sequence_counter": 0,
    }

    manifest = {
        "project": "V79.4-Chain-Tip-Integrity",
        "version": manifest_version,
    }

    return WitnessChain(
        initial_state=initial_state,
        manifest=manifest,
        witness_id=witness_id,
    )


def append_same_event(chain):
    chain.append_event(
        event_id="EVENT-001",
        event_type="TEST_EVENT",
        timestamp="2026-09-03T13:20:00Z",
        payload={
            "value": 100,
            "action": "test",
        },
        evidence={
            "document": "evidence-001",
        },
    )


def create_engine():
    return IndependentMultiWitnessEngine(
        quorum=2,
        authorized_witness_ids={
            "witness-1",
            "witness-2",
            "witness-3",
        },
    )


def test_different_manifest_hash_must_not_reach_consensus():
    """
    Өөр manifest-тай witness нь ижил STATE_ROOT-той байсан ч
    ижил Chain Tip-ийн нэг хэсэг гэж тооцогдох ёсгүй.

    V79.3 дээр энэ тест FAIL болно.
    V79.4 дээр PASS болох ёстой.
    """

    chains = [
        create_chain(
            "witness-1",
            manifest_version="1",
        ),
        create_chain(
            "witness-2",
            manifest_version="2",
        ),
        create_chain(
            "witness-3",
            manifest_version="1",
        ),
    ]

    for chain in chains:
        append_same_event(chain)

    bundles = [
        serialize_chain(chain)
        for chain in chains
    ]

    engine = create_engine()
    result = engine.evaluate(bundles)

    assert result.status == "CONSENSUS"

    assert result.votes == 2

    assert result.valid_witness_ids == [
        "witness-1",
        "witness-2",
        "witness-3",
    ]

    assert result.dissenting_witness_ids == [
        "witness-2",
    ]