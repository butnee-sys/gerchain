"""
GerChain V80.3.1
Independent Money Semantic Verifier Tests.

Purpose:
- Зөв мөнгөн шилжилт PASS болохыг шалгах.
- Буруу amount REJECT болохыг шалгах.
- Буруу source balance REJECT болохыг шалгах.
- Буруу destination balance REJECT болохыг шалгах.
- Буруу settlement currency / state REJECT болохыг шалгах.
- Дараалсан гүйлгээний үлдэгдлийн залгамж чанарыг шалгах.
- Залгамж чанар зөрчигдвөл REJECT хийх.
- Өөр валютын үлдэгдлийг тусад нь тооцохыг шалгах.
- Олон дараалсан мөнгөн шилжилт PASS болохыг шалгах.
"""

from verifier.money_semantic_verifier import (
    MoneySemanticVerifier,
)


def make_transfer(
    amount=100,
    currency="MNT",
    previous_source_balance=1000,
    new_source_balance=900,
    previous_destination_balance=0,
    new_destination_balance=100,
):
    return {
        "record": {
            "sequence": 1,
            "event_type": "MONEY_TRANSFER",
        },
        "event_payload": {
            "transaction_id": "TX-001",
            "sequence": 1,
            "source": "BUYER",
            "destination": "SELLER",
            "amount": amount,
            "currency": currency,
            "previous_source_balance": previous_source_balance,
            "new_source_balance": new_source_balance,
            "previous_destination_balance": previous_destination_balance,
            "new_destination_balance": new_destination_balance,
        },
    }


def make_settlement(
    amount=100,
    currency="MNT",
    previous_source_balance=1000,
    new_source_balance=900,
    previous_destination_balance=0,
    new_destination_balance=100,
    previous_escrow_state="LOCKED",
    new_escrow_state="RELEASED",
):
    return {
        "record": {
            "sequence": 1,
            "event_type": "ATOMIC_SETTLEMENT",
        },
        "event_payload": {
            "transaction_id": "TX-001",
            "sequence": 1,
            "source": "BUYER",
            "destination": "SELLER",
            "amount": amount,
            "currency": currency,
            "escrow_id": "ESCROW-001",
            "previous_escrow_state": previous_escrow_state,
            "new_escrow_state": new_escrow_state,
            "previous_source_balance": previous_source_balance,
            "new_source_balance": new_source_balance,
            "previous_destination_balance": previous_destination_balance,
            "new_destination_balance": new_destination_balance,
        },
    }


def make_second_transfer(
    sequence=2,
    previous_source_balance=900,
    new_source_balance=700,
    previous_destination_balance=100,
    new_destination_balance=300,
    currency="MNT",
):
    return {
        "record": {
            "sequence": sequence,
            "event_type": "MONEY_TRANSFER",
        },
        "event_payload": {
            "transaction_id": "TX-002",
            "sequence": sequence,
            "source": "BUYER",
            "destination": "SELLER",
            "amount": 200,
            "currency": currency,
            "previous_source_balance": previous_source_balance,
            "new_source_balance": new_source_balance,
            "previous_destination_balance": previous_destination_balance,
            "new_destination_balance": new_destination_balance,
        },
    }


def test_valid_money_transfer_passes():
    bundle = {
        "entries": [
            make_transfer(),
        ]
    }

    verifier = MoneySemanticVerifier()

    assert verifier.verify(bundle) is True


def test_wrong_amount_is_rejected():
    bundle = {
        "entries": [
            make_transfer(
                amount=150,
            ),
        ]
    }

    verifier = MoneySemanticVerifier()

    assert verifier.verify(bundle) is False


def test_wrong_source_balance_is_rejected():
    bundle = {
        "entries": [
            make_transfer(
                previous_source_balance=1000,
                new_source_balance=950,
            ),
        ]
    }

    verifier = MoneySemanticVerifier()

    assert verifier.verify(bundle) is False


def test_wrong_destination_balance_is_rejected():
    bundle = {
        "entries": [
            make_transfer(
                previous_destination_balance=0,
                new_destination_balance=50,
            ),
        ]
    }

    verifier = MoneySemanticVerifier()

    assert verifier.verify(bundle) is False


def test_invalid_atomic_settlement_is_rejected():
    bundle = {
        "entries": [
            make_settlement(
                currency="USD",
                previous_escrow_state="FUNDED",
            ),
        ]
    }

    verifier = MoneySemanticVerifier()

    assert verifier.verify(bundle) is False


def test_v8031_sequential_balances_pass():
    bundle = {
        "entries": [
            make_transfer(),
            make_second_transfer(),
        ]
    }

    verifier = MoneySemanticVerifier()

    assert verifier.verify(bundle) is True


def test_v8031_source_balance_continuity_is_rejected():
    bundle = {
        "entries": [
            make_transfer(),
            make_second_transfer(
                previous_source_balance=950,
                new_source_balance=750,
            ),
        ]
    }

    verifier = MoneySemanticVerifier()

    assert verifier.verify(bundle) is False


def test_v8031_destination_balance_continuity_is_rejected():
    bundle = {
        "entries": [
            make_transfer(),
            make_second_transfer(
                previous_destination_balance=50,
                new_destination_balance=250,
            ),
        ]
    }

    verifier = MoneySemanticVerifier()

    assert verifier.verify(bundle) is False


def test_v8031_currency_is_part_of_balance_continuity():
    bundle = {
        "entries": [
            make_transfer(
                currency="MNT",
            ),
            make_second_transfer(
                currency="USD",
                previous_source_balance=950,
                new_source_balance=750,
                previous_destination_balance=50,
                new_destination_balance=250,
            ),
        ]
    }

    verifier = MoneySemanticVerifier()

    assert verifier.verify(bundle) is True


def test_v8031_multiple_sequential_transfers_pass():
    bundle = {
        "entries": [
            make_transfer(
                amount=100,
                previous_source_balance=1000,
                new_source_balance=900,
                previous_destination_balance=0,
                new_destination_balance=100,
            ),
            make_second_transfer(
                sequence=2,
                previous_source_balance=900,
                new_source_balance=700,
                previous_destination_balance=100,
                new_destination_balance=300,
            ),
            {
                "record": {
                    "sequence": 3,
                    "event_type": "MONEY_TRANSFER",
                },
                "event_payload": {
                    "transaction_id": "TX-003",
                    "sequence": 3,
                    "source": "BUYER",
                    "destination": "SELLER",
                    "amount": 300,
                    "currency": "MNT",
                    "previous_source_balance": 700,
                    "new_source_balance": 400,
                    "previous_destination_balance": 300,
                    "new_destination_balance": 600,
                },
            },
        ]
    }

    verifier = MoneySemanticVerifier()

    assert verifier.verify(bundle) is True