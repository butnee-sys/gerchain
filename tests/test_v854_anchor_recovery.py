import pytest

from persistence.anchor_recovery import AnchorRecovery
from persistence.chain_tip_anchor import ChainTipAnchor


def make_tip(char: str) -> str:
    return char * 64


def make_anchor(previous_tip=None, chain_tip=None):
    return ChainTipAnchor(
        chain_tip=chain_tip or make_tip('b'),
        previous_tip=previous_tip,
    ).to_dict()


def test_valid_genesis_anchor_recovery():
    tip = make_tip('a')
    data = make_anchor(chain_tip=tip)
    result = AnchorRecovery.verify_anchor(data, recovered_chain_tip=tip)
    assert result['status'] == 'VALID'
    assert result['accepted'] is True
    assert result['chain_tip_valid'] is True
    assert result['previous_tip_valid'] is True
    assert result['anchor_hash_valid'] is True


def test_valid_linked_anchor_recovery():
    previous = make_tip('a')
    tip = make_tip('b')
    data = make_anchor(previous_tip=previous, chain_tip=tip)
    result = AnchorRecovery.verify_anchor(
        data,
        recovered_chain_tip=tip,
        expected_previous_tip=previous,
    )
    assert result['status'] == 'VALID'
    assert result['accepted'] is True


def test_recovered_chain_tip_mismatch_rejected():
    tip = make_tip('a')
    wrong_tip = make_tip('b')
    data = make_anchor(chain_tip=tip)
    result = AnchorRecovery.verify_anchor(data, recovered_chain_tip=wrong_tip)
    assert result['status'] == 'REJECTED'
    assert result['accepted'] is False
    assert result['chain_tip_valid'] is False


def test_previous_tip_mismatch_rejected():
    previous = make_tip('a')
    wrong_previous = make_tip('c')
    tip = make_tip('b')
    data = make_anchor(previous_tip=previous, chain_tip=tip)
    result = AnchorRecovery.verify_anchor(
        data,
        recovered_chain_tip=tip,
        expected_previous_tip=wrong_previous,
    )
    assert result['status'] == 'REJECTED'
    assert result['accepted'] is False
    assert result['previous_tip_valid'] is False


def test_anchor_hash_tamper_rejected():
    tip = make_tip('a')
    data = make_anchor(chain_tip=tip)
    data['anchor_hash'] = make_tip('f')
    result = AnchorRecovery.verify_anchor(data, recovered_chain_tip=tip)
    assert result['status'] == 'REJECTED'
    assert result['accepted'] is False


def test_chain_tip_tamper_rejected():
    original_tip = make_tip('a')
    tampered_tip = make_tip('f')
    data = make_anchor(chain_tip=original_tip)
    data['chain_tip'] = tampered_tip
    result = AnchorRecovery.verify_anchor(
        data,
        recovered_chain_tip=tampered_tip,
    )
    assert result['status'] == 'REJECTED'
    assert result['accepted'] is False


def test_missing_anchor_hash_rejected():
    tip = make_tip('a')
    data = make_anchor(chain_tip=tip)
    del data['anchor_hash']
    result = AnchorRecovery.verify_anchor(data, recovered_chain_tip=tip)
    assert result['status'] == 'REJECTED'
    assert result['accepted'] is False


def test_invalid_anchor_version_rejected():
    tip = make_tip('a')
    data = make_anchor(chain_tip=tip)
    data['version'] = 'V99.9'
    result = AnchorRecovery.verify_anchor(data, recovered_chain_tip=tip)
    assert result['status'] == 'REJECTED'
    assert result['accepted'] is False
    assert result['reason'] == 'ANCHOR_INVALID'


def test_invalid_anchor_type_rejected():
    with pytest.raises(TypeError):
        AnchorRecovery.verify_anchor(
            anchor_data='invalid',
            recovered_chain_tip=make_tip('a'),
        )


def test_recovered_chain_tip_type_rejected():
    tip = make_tip('a')
    data = make_anchor(chain_tip=tip)
    with pytest.raises(TypeError):
        AnchorRecovery.verify_anchor(
            data,
            recovered_chain_tip=123,
        )
