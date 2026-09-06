"""
GerChain V79.7
Persistent Chain Tip Anchor Tests.

Purpose:
- Баталгаатай CHAIN_TIP-ийг тусдаа anchor болгон хадгалах.
- Дахин уншсан chain-ийг anchor-той харьцуулах.
- Chain өөрчлөгдвөл anchor mismatch илрүүлэх.
- Anchor өөрчлөгдвөл integrity failure илрүүлэх.
"""

import copy
import json

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
        "project": "V79.7-Persistent-Chain-Tip-Anchor",
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
        timestamp="2026-09-03T15:20:00Z",
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
        timestamp="2026-09-03T15:21:00Z",
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


def decode(data):
    return json.loads(
        data.decode("utf-8")
    )


def get_bundle_and_tip():
    chain = create_chain()
    engine = create_engine()

    bundle = decode(
        serialize_chain(chain)
    )

    assert engine.verifier.verify_bundle(
        bundle
    )

    chain_tip = engine.compute_chain_tip(
        bundle
    )

    assert chain_tip is not None

    return engine, bundle, chain_tip


def test_persistent_anchor_matches_chain_tip():
    """
    Хадгалсан Anchor нь тухайн Chain Tip-тэй
    яг адил байх ёстой.
    """

    engine, bundle, chain_tip = (
        get_bundle_and_tip()
    )

    anchor = {
        "chain_tip": chain_tip,
    }

    assert anchor["chain_tip"] == (
        engine.compute_chain_tip(bundle)
    )


def test_reloaded_chain_matches_persistent_anchor():
    """
    Chain-ийг дахин уншсаны дараа
    шинэчилж тооцсон Chain Tip нь
    хадгалсан Anchor-той адил байна.
    """

    engine, bundle, chain_tip = (
        get_bundle_and_tip()
    )

    anchor = {
        "chain_tip": chain_tip,
    }

    reloaded_bundle = decode(
        json.dumps(
            bundle,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    )

    reloaded_tip = engine.compute_chain_tip(
        reloaded_bundle
    )

    assert reloaded_tip == (
        anchor["chain_tip"]
    )


def test_changed_history_does_not_match_anchor():
    """
    Chain-ийн түүх өөрчлөгдвөл
    шинэ Chain Tip нь хуучин Anchor-той
    таарах ёсгүй.
    """

    engine, bundle, chain_tip = (
        get_bundle_and_tip()
    )

    anchor = {
        "chain_tip": chain_tip,
    }

    tampered = copy.deepcopy(bundle)

    tampered["entries"][0][
        "event_payload"
    ]["value"] = 999999

    assert not engine.verifier.verify_bundle(
        tampered
    )

    assert engine.compute_chain_tip(
        tampered
    ) is None


def test_changed_anchor_does_not_match_chain():
    """
    Anchor өөрчлөгдвөл тухайн Chain-тэй
    таарахгүй байх ёстой.
    """

    engine, bundle, chain_tip = (
        get_bundle_and_tip()
    )

    anchor = {
        "chain_tip": chain_tip,
    }

    tampered_anchor = copy.deepcopy(
        anchor
    )

    tampered_anchor["chain_tip"] = (
        "0" * 64
    )

    assert tampered_anchor[
        "chain_tip"
    ] != engine.compute_chain_tip(
        bundle
    )


def test_anchor_has_canonical_hash_format():
    """
    Anchor дахь Chain Tip нь canonical
    SHA-256 hex хэлбэртэй байна.
    """

    _, _, chain_tip = get_bundle_and_tip()

    assert isinstance(
        chain_tip,
        str,
    )

    assert len(chain_tip) == 64

    int(chain_tip, 16)
def test_anchor_disk_round_trip():
    """
    Anchor-ийг дискэнд хадгалаад буцаан уншихад
    Chain Tip өөрчлөгдөх ёсгүй.
    """

    from persistence.chain_tip_anchor import ChainTipAnchor

    _, _, chain_tip = get_bundle_and_tip()

    anchor = ChainTipAnchor(chain_tip)

    path = "tests/.tmp_chain_tip_anchor_v797"

    anchor.save(path)

    loaded = ChainTipAnchor.load(path)

    assert loaded.chain_tip == chain_tip
    assert loaded.verify(chain_tip)

    import os

    os.remove(path)


def test_modified_anchor_is_rejected():
    """
    Дискэнд хадгалсан Anchor-ийг өөрчилбөл
    жинхэнэ Chain Tip-тэй таарах ёсгүй.
    """

    from persistence.chain_tip_anchor import ChainTipAnchor

    _, _, chain_tip = get_bundle_and_tip()

    anchor = ChainTipAnchor(chain_tip)

    path = "tests/.tmp_chain_tip_anchor_tampered_v797"

    anchor.save(path)

    tampered = ChainTipAnchor.load(path)

    tampered.chain_tip = "0" * 64

    assert not tampered.verify(chain_tip)

    import os

    os.remove(path)


def test_anchor_rejects_invalid_hash():
    """
    64 тэмдэгт боловч hex биш утгыг Anchor
    хүлээн авах ёсгүй.
    """

    from persistence.chain_tip_anchor import ChainTipAnchor

    invalid_tip = "Z" * 64

    try:
        ChainTipAnchor(invalid_tip)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Invalid Chain Tip was accepted."
        )


def test_anchor_version_is_preserved():
    """
    Anchor хадгалах болон сэргээх үед хувилбар
    өөрчлөгдөхгүй байх ёстой.
    """

    from persistence.chain_tip_anchor import ChainTipAnchor

    _, _, chain_tip = get_bundle_and_tip()

    anchor = ChainTipAnchor(chain_tip)

    path = "tests/.tmp_chain_tip_anchor_version_v797"

    anchor.save(path)

    loaded = ChainTipAnchor.load(path)

    assert loaded.to_dict()["version"] == (
        ChainTipAnchor.VERSION
    )

    import os

    os.remove(path)