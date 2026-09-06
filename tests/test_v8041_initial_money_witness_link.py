"""
GerChain V80.4.1
Initial Money State -> WitnessChain Link Tests.

Purpose:
- Эхний мөнгөний төлөвийн хэшийг WitnessChain-д холбоно.
- Witness event payload дотор commitment хадгалагдаж байгааг шалгана.
- Эхний мөнгөний төлөв өөрчлөгдвөл commitment зөрөхийг илрүүлнэ.
- Одоогийн Witness cryptographic verification-ийг ашиглана.
"""

from core.hashing import domain_hash
from verifier.independent_verifier import IndependentVerifier
from witness.chain import WitnessChain


def make_initial_state():
    return {
        "currency": "MNT",
        "balances": {
            "BUYER": 1000,
            "SELLER": 0,
        },
    }


def make_witness_chain():
    return WitnessChain(
        initial_state={
            "value": 0,
            "sequence_counter": 0,
            "initialized": False,
        },
        manifest={
            "system": "GerChain",
            "version": "V80.4.1",
            "purpose": "Initial Money State Commitment",
        },
        witness_id="WITNESS-MONEY-INITIAL-001",
    )


def make_commitment(state):
    return {
        "state": state,
        "state_hash": domain_hash(
            "INITIAL_MONEY_STATE",
            state,
        ),
    }


def test_initial_money_commitment_is_witnessed():

    chain = make_witness_chain()
    state = make_initial_state()

    commitment = make_commitment(state)

    record = chain.append_event(
        event_id="INITIAL-MONEY-001",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T05:00:01",
        payload=commitment,
        evidence={
            "type": "INITIAL_MONEY_STATE",
            "reference": "MONEY-INITIAL-001",
        },
    )

    assert record.event_type == "INITIAL_MONEY_STATE"
    assert len(chain.entries) == 1

    payload = (
        chain.entries[0]
        .event_payload
    )

    assert payload["state"] == state

    assert payload["state_hash"] == domain_hash(
        "INITIAL_MONEY_STATE",
        state,
    )


def test_initial_money_commitment_detects_balance_tamper():

    chain = make_witness_chain()
    state = make_initial_state()

    commitment = make_commitment(state)

    chain.append_event(
        event_id="INITIAL-MONEY-002",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T05:00:02",
        payload=commitment,
        evidence={
            "type": "INITIAL_MONEY_STATE",
            "reference": "MONEY-INITIAL-002",
        },
    )

    stored_state = (
        chain.entries[0]
        .event_payload["state"]
    )

    stored_hash = (
        chain.entries[0]
        .event_payload["state_hash"]
    )

    stored_state["balances"]["BUYER"] = 900

    recalculated_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        stored_state,
    )

    assert recalculated_hash != stored_hash


def test_initial_money_commitment_detects_currency_tamper():

    chain = make_witness_chain()
    state = make_initial_state()

    commitment = make_commitment(state)

    chain.append_event(
        event_id="INITIAL-MONEY-003",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T05:00:03",
        payload=commitment,
        evidence={
            "type": "INITIAL_MONEY_STATE",
            "reference": "MONEY-INITIAL-003",
        },
    )

    stored_state = (
        chain.entries[0]
        .event_payload["state"]
    )

    stored_hash = (
        chain.entries[0]
        .event_payload["state_hash"]
    )

    stored_state["currency"] = "USD"

    recalculated_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        stored_state,
    )

    assert recalculated_hash != stored_hash


def test_witness_chain_still_passes_independent_verification():

    chain = make_witness_chain()
    state = make_initial_state()

    commitment = make_commitment(state)

    chain.append_event(
        event_id="INITIAL-MONEY-004",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T05:00:04",
        payload=commitment,
        evidence={
            "type": "INITIAL_MONEY_STATE",
            "reference": "MONEY-INITIAL-004",
        },
    )

    from persistence.serializer import serialize_chain

    serialized = serialize_chain(chain)

    import json

    bundle = json.loads(
        serialized.decode("utf-8")
    )

    verifier = IndependentVerifier()

    assert (
        verifier.verify_bundle(bundle)
        is True
    )