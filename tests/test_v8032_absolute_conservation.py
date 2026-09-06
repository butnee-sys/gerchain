"""
GerChain V80.3.2
Absolute Money Conservation Tests.

Purpose:
- Баталгаатай эхний дансны үлдэгдлийг ашиглах.
- Эцсийн үлдэгдлийг эхний үлдэгдэлтэй харьцуулах.
- Мөнгө шинээр бий болгосон төлөвийг REJECT хийх.
- Мөнгө устгасан төлөвийг REJECT хийх.
- Олон дансны мөнгөний хадгалалтыг шалгах.
"""


def make_transfer(
    amount=100,
    previous_source_balance=1000,
    new_source_balance=900,
    previous_destination_balance=0,
    new_destination_balance=100,
    currency="MNT",
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


def make_bundle(
    entries,
    initial_balances,
):
    return {
        "initial_balances": initial_balances,
        "entries": entries,
    }


def verify_absolute_conservation(bundle):
    """
    V80.3.2:

    Баталгаатай эхний үлдэгдэл:

        BUYER  = 1000
        SELLER = 0

    Эцсийн үлдэгдэл:

        BUYER  = 900
        SELLER = 100

    Нийт:

        1000 = 1000
    """

    initial_balances = bundle.get(
        "initial_balances"
    )

    entries = bundle.get("entries")

    if not isinstance(initial_balances, dict):
        return False

    if not isinstance(entries, list):
        return False

    final_balances = {}

    for entry in entries:

        if not isinstance(entry, dict):
            return False

        payload = entry.get("event_payload")

        if not isinstance(payload, dict):
            return False

        source = payload.get("source")
        destination = payload.get("destination")
        currency = payload.get("currency")

        new_source_balance = payload.get(
            "new_source_balance"
        )

        new_destination_balance = payload.get(
            "new_destination_balance"
        )

        if not isinstance(source, str):
            return False

        if not isinstance(destination, str):
            return False

        if not isinstance(currency, str):
            return False

        if not isinstance(
            new_source_balance,
            int,
        ):
            return False

        if not isinstance(
            new_destination_balance,
            int,
        ):
            return False

        if new_source_balance < 0:
            return False

        if new_destination_balance < 0:
            return False

        source_key = (
            source,
            currency,
        )

        destination_key = (
            destination,
            currency,
        )

        final_balances[source_key] = (
            new_source_balance
        )

        final_balances[destination_key] = (
            new_destination_balance
        )

    initial_totals = {}

    for key, balance in initial_balances.items():

        if not isinstance(key, tuple):
            return False

        if len(key) != 2:
            return False

        account, currency = key

        if not isinstance(account, str):
            return False

        if not isinstance(currency, str):
            return False

        if not isinstance(balance, int):
            return False

        if balance < 0:
            return False

        initial_totals.setdefault(
            currency,
            0,
        )

        initial_totals[currency] += balance

    final_totals = {}

    for key, balance in final_balances.items():

        account, currency = key

        final_totals.setdefault(
            currency,
            0,
        )

        final_totals[currency] += balance

    currencies = (
        set(initial_totals)
        | set(final_totals)
    )

    for currency in currencies:

        if (
            initial_totals.get(currency, 0)
            != final_totals.get(currency, 0)
        ):
            return False

    return True


def test_absolute_conservation_passes():

    bundle = make_bundle(
        entries=[
            make_transfer(),
        ],
        initial_balances={
            ("BUYER", "MNT"): 1000,
            ("SELLER", "MNT"): 0,
        },
    )

    assert (
        verify_absolute_conservation(bundle)
        is True
    )


def test_money_creation_is_rejected():

    bundle = make_bundle(
        entries=[
            make_transfer(
                new_destination_balance=200,
            ),
        ],
        initial_balances={
            ("BUYER", "MNT"): 1000,
            ("SELLER", "MNT"): 0,
        },
    )

    assert (
        verify_absolute_conservation(bundle)
        is False
    )


def test_money_destruction_is_rejected():

    bundle = make_bundle(
        entries=[
            make_transfer(
                new_source_balance=800,
            ),
        ],
        initial_balances={
            ("BUYER", "MNT"): 1000,
            ("SELLER", "MNT"): 0,
        },
    )

    assert (
        verify_absolute_conservation(bundle)
        is False
    )


def test_wrong_authoritative_initial_balance_is_rejected():

    bundle = make_bundle(
        entries=[
            make_transfer(),
        ],
        initial_balances={
            ("BUYER", "MNT"): 900,
            ("SELLER", "MNT"): 0,
        },
    )

    assert (
        verify_absolute_conservation(bundle)
        is False
    )


def test_multiple_accounts_preserve_total_money():

    entries = [
        make_transfer(
            amount=100,
            previous_source_balance=1000,
            new_source_balance=900,
            previous_destination_balance=0,
            new_destination_balance=100,
        ),
        {
            "record": {
                "sequence": 2,
                "event_type": "MONEY_TRANSFER",
            },
            "event_payload": {
                "transaction_id": "TX-002",
                "sequence": 2,
                "source": "SELLER",
                "destination": "FARMER",
                "amount": 100,
                "currency": "MNT",
                "previous_source_balance": 100,
                "new_source_balance": 0,
                "previous_destination_balance": 0,
                "new_destination_balance": 100,
            },
        },
    ]

    bundle = make_bundle(
        entries=entries,
        initial_balances={
            ("BUYER", "MNT"): 1000,
            ("SELLER", "MNT"): 0,
            ("FARMER", "MNT"): 0,
        },
    )

    assert (
        verify_absolute_conservation(bundle)
        is True
    )