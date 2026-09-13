"""Cross-cutting DEE Trinity protection invariants."""

import pytest

from dee_security.trinity import TrinityDimension, TrinityError, evaluate_trinity, require_trinity


def test_trinity_requires_all_three_dimensions():
    decision = evaluate_trinity(trust=True, transparency=True, performance=True)
    assert decision.allowed is True
    decision.require_allowed()


@pytest.mark.parametrize(
    "missing",
    [TrinityDimension.TRUST.value, TrinityDimension.TRANSPARENCY.value, TrinityDimension.PERFORMANCE.value],
)
def test_trinity_fails_closed_when_one_dimension_fails(missing):
    proof = {
        TrinityDimension.TRUST.value: True,
        TrinityDimension.TRANSPARENCY.value: True,
        TrinityDimension.PERFORMANCE.value: True,
    }
    proof[missing] = False

    with pytest.raises(TrinityError, match="DEE Trinity denied"):
        require_trinity(proof)


def test_trinity_fails_closed_when_dimension_is_missing():
    with pytest.raises(TrinityError, match="TRUST"):
        require_trinity({
            TrinityDimension.TRANSPARENCY.value: True,
            TrinityDimension.PERFORMANCE.value: True,
        })


def test_trinity_is_not_escrow_specific():
    """The policy accepts a generic protected operation proof."""
    decision = require_trinity({
        "TRUST": True,
        "TRANSPARENCY": True,
        "PERFORMANCE": True,
        "operation": "adapter-registration",
    })
    assert decision.allowed is True
