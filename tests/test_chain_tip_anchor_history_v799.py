"""
GerChain V79.9
Anchor History Integrity Tests.

Purpose:
- Anchor-уудыг дараалсан түүх болгон шалгах.
- Anchor бүрийн previous_tip нь өмнөх anchor-ийн
  chain_tip-тэй яг таарч байгаа эсэхийг шалгах.
- Anchor-ийн дараалал эвдэрвэл REJECT хийх.
- Дундаас Anchor устгагдвал REJECT хийх.
- Anchor-ийн chain_tip өөрчлөгдвөл REJECT хийх.
- Anchor-ийн previous_tip өөрчлөгдвөл REJECT хийх.
"""

from core.hashing import domain_hash


def compute_anchor_hash(
    previous_tip,
    chain_tip,
):
    return domain_hash(
        "CHAIN_TIP_ANCHOR",
        {
            "previous_tip": previous_tip,
            "chain_tip": chain_tip,
        },
    )


def verify_anchor_history(anchors):
    """
    Anchor history-г эхнээс нь бие даан шалгана.

    Дараалал:
        Anchor_0.previous_tip = None
        Anchor_N.previous_tip = Anchor_(N-1).chain_tip
    """

    if not isinstance(anchors, list):
        return False

    if not anchors:
        return False

    previous_tip = None

    for anchor in anchors:

        if not isinstance(anchor, dict):
            return False

        if anchor.get("previous_tip") != previous_tip:
            return False

        chain_tip = anchor.get("chain_tip")

        if not isinstance(chain_tip, str):
            return False

        expected_hash = compute_anchor_hash(
            previous_tip,
            chain_tip,
        )

        if anchor.get("anchor_hash") != expected_hash:
            return False

        previous_tip = chain_tip

    return True


def make_anchor(
    previous_tip,
    chain_tip,
):
    return {
        "previous_tip": previous_tip,
        "chain_tip": chain_tip,
        "anchor_hash": compute_anchor_hash(
            previous_tip,
            chain_tip,
        ),
    }


def test_valid_anchor_history_passes():
    tip_a = "1" * 64
    tip_b = "2" * 64
    tip_c = "3" * 64

    anchors = [
        make_anchor(None, tip_a),
        make_anchor(tip_a, tip_b),
        make_anchor(tip_b, tip_c),
    ]

    assert verify_anchor_history(anchors)


def test_broken_previous_tip_is_rejected():
    tip_a = "1" * 64
    tip_b = "2" * 64
    tip_c = "3" * 64

    anchors = [
        make_anchor(None, tip_a),
        make_anchor("9" * 64, tip_b),
        make_anchor(tip_b, tip_c),
    ]

    assert not verify_anchor_history(anchors)


def test_deleted_middle_anchor_is_rejected():
    tip_a = "1" * 64
    tip_b = "2" * 64
    tip_c = "3" * 64

    anchors = [
        make_anchor(None, tip_a),
        make_anchor(tip_b, tip_c),
    ]

    assert not verify_anchor_history(anchors)


def test_modified_chain_tip_is_rejected():
    tip_a = "1" * 64
    tip_b = "2" * 64

    anchors = [
        make_anchor(None, tip_a),
        make_anchor(tip_a, tip_b),
    ]

    anchors[1]["chain_tip"] = "8" * 64

    assert not verify_anchor_history(anchors)


def test_modified_previous_tip_is_rejected():
    tip_a = "1" * 64
    tip_b = "2" * 64

    anchors = [
        make_anchor(None, tip_a),
        make_anchor(tip_a, tip_b),
    ]

    anchors[1]["previous_tip"] = "7" * 64

    assert not verify_anchor_history(anchors)


def test_modified_anchor_hash_is_rejected():
    tip_a = "1" * 64
    tip_b = "2" * 64

    anchors = [
        make_anchor(None, tip_a),
        make_anchor(tip_a, tip_b),
    ]

    anchors[1]["anchor_hash"] = "f" * 64

    assert not verify_anchor_history(anchors)


def test_reordered_anchor_history_is_rejected():
    tip_a = "1" * 64
    tip_b = "2" * 64
    tip_c = "3" * 64

    anchors = [
        make_anchor(None, tip_a),
        make_anchor(tip_a, tip_b),
        make_anchor(tip_b, tip_c),
    ]

    reordered = [
        anchors[0],
        anchors[2],
        anchors[1],
    ]

    assert not verify_anchor_history(reordered)


def test_extra_anchor_after_valid_history_is_detected():
    tip_a = "1" * 64
    tip_b = "2" * 64
    tip_c = "3" * 64
    tip_d = "4" * 64

    anchors = [
        make_anchor(None, tip_a),
        make_anchor(tip_a, tip_b),
        make_anchor(tip_b, tip_c),
    ]

    anchors.append(
        make_anchor(tip_c, tip_d)
    )

    assert verify_anchor_history(anchors)