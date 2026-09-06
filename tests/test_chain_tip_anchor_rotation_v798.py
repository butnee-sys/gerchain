"""
GerChain V79.8
Anchor Rotation & Previous-Tip Linking Tests.

Purpose:
- First Anchor нь previous_tip=None байхыг батлах.
- Previous Tip -> New Chain Tip холбоосыг бодитоор шалгах.
- Anchor hash deterministic байхыг шалгах.
- Previous Tip өөрчлөгдвөл холбоос хүчингүй болохыг шалгах.
- Chain Tip өөрчлөгдвөл холбоос хүчингүй болохыг шалгах.
- Anchor hash tamper илрүүлэх.
- Disk round-trip холбоосыг хадгалах.
- A -> B -> C rotation chain дарааллыг шалгах.
"""

import json

import pytest

from core.hashing import domain_hash
from persistence.chain_tip_anchor import ChainTipAnchor


def compute_rotation_anchor(
    previous_tip,
    new_chain_tip,
):
    """
    Previous Tip + New Chain Tip-ээс
    canonical Anchor hash үүсгэнэ.
    """

    return domain_hash(
        "CHAIN_TIP_ANCHOR",
        {
            "previous_tip": previous_tip,
            "chain_tip": new_chain_tip,
        },
    )


def test_first_anchor_has_no_previous_tip():
    """Анхны Anchor нь өмнөх Tip-гүй байна."""

    chain_tip = "1" * 64

    anchor = ChainTipAnchor(
        chain_tip=chain_tip,
    )

    assert anchor.previous_tip is None
    assert anchor.chain_tip == chain_tip
    assert len(anchor.anchor_hash) == 64


def test_real_previous_tip_link_is_preserved():
    """Previous Tip -> New Chain Tip холбоос бодитоор хадгалагдана."""

    previous_tip = "1" * 64
    new_tip = "2" * 64

    anchor = ChainTipAnchor(
        chain_tip=new_tip,
        previous_tip=previous_tip,
    )

    assert anchor.previous_tip == previous_tip
    assert anchor.chain_tip == new_tip

    assert anchor.verify_link(
        previous_tip,
        new_tip,
    )


def test_anchor_hash_is_deterministic():
    """Ижил холбоос үргэлж ижил Anchor hash үүсгэнэ."""

    previous_tip = "1" * 64
    new_tip = "2" * 64

    anchor_1 = ChainTipAnchor(
        chain_tip=new_tip,
        previous_tip=previous_tip,
    )

    anchor_2 = ChainTipAnchor(
        chain_tip=new_tip,
        previous_tip=previous_tip,
    )

    assert anchor_1.anchor_hash == anchor_2.anchor_hash

    assert anchor_1.anchor_hash == compute_rotation_anchor(
        previous_tip,
        new_tip,
    )


def test_modified_previous_tip_is_rejected():
    """Previous Tip өөрчлөгдвөл холбоос хүчингүй болно."""

    previous_tip = "1" * 64
    new_tip = "2" * 64

    anchor = ChainTipAnchor(
        chain_tip=new_tip,
        previous_tip=previous_tip,
    )

    assert anchor.verify_link(
        previous_tip,
        new_tip,
    )

    assert not anchor.verify_link(
        "3" * 64,
        new_tip,
    )


def test_modified_chain_tip_is_rejected():
    """New Chain Tip өөрчлөгдвөл холбоос хүчингүй болно."""

    previous_tip = "1" * 64
    new_tip = "2" * 64

    anchor = ChainTipAnchor(
        chain_tip=new_tip,
        previous_tip=previous_tip,
    )

    assert anchor.verify_link(
        previous_tip,
        new_tip,
    )

    assert not anchor.verify_link(
        previous_tip,
        "4" * 64,
    )


def test_tampered_anchor_hash_is_rejected():
    """Сериалчилсан Anchor-ийн hash өөрчлөгдвөл REJECT болно."""

    previous_tip = "1" * 64
    new_tip = "2" * 64

    anchor = ChainTipAnchor(
        chain_tip=new_tip,
        previous_tip=previous_tip,
    )

    data = anchor.to_dict()

    data["anchor_hash"] = "f" * 64

    with pytest.raises(ValueError):
        ChainTipAnchor.from_dict(data)


def test_disk_round_trip_preserves_rotation_link(
    tmp_path,
):
    """Дискний round-trip нь Previous Tip холбоосыг хадгална."""

    previous_tip = "1" * 64
    new_tip = "2" * 64

    anchor = ChainTipAnchor(
        chain_tip=new_tip,
        previous_tip=previous_tip,
    )

    path = tmp_path / "chain_tip_anchor.json"

    anchor.save(path)

    loaded = ChainTipAnchor.load(path)

    assert loaded.previous_tip == previous_tip
    assert loaded.chain_tip == new_tip
    assert loaded.anchor_hash == anchor.anchor_hash

    assert loaded.verify_link(
        previous_tip,
        new_tip,
    )


def test_rotation_chain_a_to_b_to_c():
    """
    A -> B -> C дараалсан Anchor rotation
    зөв холбогдож байгаа эсэх.
    """

    tip_a = "1" * 64
    tip_b = "2" * 64
    tip_c = "3" * 64

    anchor_a = ChainTipAnchor(
        chain_tip=tip_a,
        previous_tip=None,
    )

    anchor_b = ChainTipAnchor(
        chain_tip=tip_b,
        previous_tip=tip_a,
    )

    anchor_c = ChainTipAnchor(
        chain_tip=tip_c,
        previous_tip=tip_b,
    )

    assert anchor_a.verify_link(
        None,
        tip_a,
    )

    assert anchor_b.verify_link(
        tip_a,
        tip_b,
    )

    assert anchor_c.verify_link(
        tip_b,
        tip_c,
    )

    assert anchor_b.anchor_hash != anchor_c.anchor_hash


def test_serialized_anchor_contains_rotation_fields():
    """Canonical serialization нь rotation-ийн хоёр Tip-ийг агуулна."""

    previous_tip = "1" * 64
    new_tip = "2" * 64

    anchor = ChainTipAnchor(
        chain_tip=new_tip,
        previous_tip=previous_tip,
    )

    decoded = json.loads(
        anchor.to_bytes().decode("utf-8")
    )

    assert decoded["version"] == "V79.8"
    assert decoded["previous_tip"] == previous_tip
    assert decoded["chain_tip"] == new_tip
    assert decoded["anchor_hash"] == anchor.anchor_hash