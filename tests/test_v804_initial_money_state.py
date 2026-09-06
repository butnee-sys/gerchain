"""
GerChain V80.4
Initial Money State Cryptographic Commitment Tests.

Purpose:
- Эхний мөнгөний төлөвийг тодорхойлох.
- Эхний төлөвийн криптографийн хэш үүсгэх.
- Дараа нь эхний төлөв өөрчлөгдсөн эсэхийг илрүүлэх.
- Бие даасан шалгагч эхний мөнгөний төлөвийн
  бүрэн бүтэн байдлыг шалгах үндэс тавих.
"""

from core.hashing import domain_hash


def make_initial_money_state():
    return {
        "currency": "MNT",
        "balances": {
            "BUYER": 1000,
            "SELLER": 0,
        },
    }


def test_initial_money_state_hash_is_deterministic():

    state = make_initial_money_state()

    hash_1 = domain_hash(
        "INITIAL_MONEY_STATE",
        state,
    )

    hash_2 = domain_hash(
        "INITIAL_MONEY_STATE",
        state,
    )

    assert hash_1 == hash_2
    assert isinstance(hash_1, str)
    assert len(hash_1) == 64


def test_initial_money_state_hash_changes_when_balance_changes():

    state = make_initial_money_state()

    original_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        state,
    )

    state["balances"]["BUYER"] = 900

    tampered_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        state,
    )

    assert tampered_hash != original_hash


def test_initial_money_state_hash_changes_when_currency_changes():

    state = make_initial_money_state()

    original_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        state,
    )

    state["currency"] = "USD"

    tampered_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        state,
    )

    assert tampered_hash != original_hash


def test_initial_money_state_requires_explicit_commitment():

    state = make_initial_money_state()

    commitment = {
        "state": state,
        "state_hash": domain_hash(
            "INITIAL_MONEY_STATE",
            state,
        ),
    }

    assert commitment["state_hash"] == domain_hash(
        "INITIAL_MONEY_STATE",
        commitment["state"],
    )