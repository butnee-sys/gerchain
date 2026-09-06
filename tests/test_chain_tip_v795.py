"""
GerChain V79.5
Canonical Chain Tip Tests.

Purpose:
- Chain Tip-ийг нэг стандарт криптографийн хэш болгон тогтоох.
- Chain Tip нь manifest_hash, final_sequence,
  final_state_hash, STATE_ROOT гэсэн бүх үндсэн бүрэлдэхүүнийг
  хамардаг болохыг батлах.
- Түүхийн аль нэг хэсэг өөрчлөгдвөл Chain Tip өөрчлөгдөхийг батлах.
"""

from core.hashing import domain_hash
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
        "project": "V79.5-Canonical-Chain-Tip",
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


def expected_chain_tip(
    manifest_hash,
    final_sequence,
    final_state_hash,
    state_root,
):
    return domain_hash(
        "CHAIN_TIP",
        {
            "manifest_hash": manifest_hash,
            "final_sequence": final_sequence,
            "final_state_hash": final_state_hash,
            "state_root": state_root,
        },
    )


def test_canonical_chain_tip_is_single_hash():
    """
    Ижил гинжийн хувьд Chain Tip нь тогтвортой,
    нэг стандарт хэш байх ёстой.
    """

    chain = create_chain("witness-1")

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

    bundle = serialize_chain(chain)

    engine = create_engine()

    decoded = engine._decode_bundle(bundle)

    assert decoded is not None

    recomputed = engine.verifier._recompute_bundle(
        decoded
    )

    assert recomputed is not None

    expected = expected_chain_tip(
        manifest_hash=decoded["manifest_hash"],
        final_sequence=recomputed["final_sequence"],
        final_state_hash=recomputed["final_state_hash"],
        state_root=recomputed["state_root"],
    )

    actual = engine.compute_chain_tip(
        decoded
    )

    assert actual == expected
    assert isinstance(actual, str)
    assert len(actual) == 64


def test_chain_tip_changes_when_history_changes():
    """
    Түүх өөрчлөгдвөл эцсийн Chain Tip заавал өөрчлөгдөнө.
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

    engine = create_engine()

    bundle_1 = engine._decode_bundle(
        serialize_chain(chain_1)
    )

    bundle_2 = engine._decode_bundle(
        serialize_chain(chain_2)
    )

    assert bundle_1 is not None
    assert bundle_2 is not None

    tip_1 = engine.compute_chain_tip(
        bundle_1
    )

    tip_2 = engine.compute_chain_tip(
        bundle_2
    )

    assert tip_1 != tip_2


def test_same_chain_tip_reaches_consensus():
    """
    Ижил Chain Tip-тэй хоёр зөвшөөрөгдсөн гэрч
    quorum бүрдүүлж зөвшилцөлд хүрнэ.
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

    engine = create_engine()

    result = engine.evaluate(
        [
            serialize_chain(chain_1),
            serialize_chain(chain_2),
        ]
    )

    assert result.status == "CONSENSUS"
    assert result.votes == 2
    assert result.consensus_hash is not None
    assert len(result.consensus_hash) == 64