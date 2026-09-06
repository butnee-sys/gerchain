"""
GerChain V80.4.2
Initial Money State Commitment Integration Tests.

Purpose:
- WitnessChain дээр эхний мөнгөний төлөвийг
  албан ёсоор commitment хэлбэрээр хадгалах.
- Эхний төлөвийн hash-ийг дахин тооцож шалгах.
- Төлөв өөрчлөгдвөл commitment зөрөхийг илрүүлэх.
- Commitment нь WitnessChain-ийн анхны төлөвийн
  бүртгэлтэй уялдаж байгааг шалгах.
"""

from core.hashing import domain_hash
from witness.chain import WitnessChain


def make_initial_money_state():
    return {
        "currency": "MNT",
        "balances": {
            "BUYER": 1000,
            "SELLER": 0,
        },
    }


def make_chain():
    return WitnessChain(
        initial_state={
            "value": 0,
            "sequence_counter": 0,
            "initialized": False,
        },
        manifest={
            "system": "GerChain",
            "version": "V80.4.2",
            "purpose": "Money State Commitment",
        },
        witness_id="WITNESS-MONEY-COMMITMENT-001",
    )


def test_initial_money_state_commitment_is_deterministic():

    state = make_initial_money_state()

    commitment_1 = domain_hash(
        "INITIAL_MONEY_STATE",
        state,
    )

    commitment_2 = domain_hash(
        "INITIAL_MONEY_STATE",
        state,
    )

    assert commitment_1 == commitment_2
    assert len(commitment_1) == 64


def test_initial_money_state_can_be_attached_to_chain():

    chain = make_chain()
    state = make_initial_money_state()

    state_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        state,
    )

    record = chain.append_event(
        event_id="INITIAL-MONEY-STATE-001",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T06:00:01",
        payload={
            "currency": state["currency"],
            "balances": state["balances"],
            "state_hash": state_hash,
        },
        evidence={
            "type": "INITIAL_MONEY_COMMITMENT",
            "reference": "MONEY-COMMITMENT-001",
        },
    )

    assert record.event_type == "INITIAL_MONEY_STATE"

    stored_payload = (
        chain.entries[0]
        .event_payload
    )

    reconstructed_state = {
        "currency": stored_payload["currency"],
        "balances": stored_payload["balances"],
    }

    assert stored_payload["state_hash"] == domain_hash(
        "INITIAL_MONEY_STATE",
        reconstructed_state,
    )


def test_initial_money_state_tampering_is_detected():

    chain = make_chain()
    state = make_initial_money_state()

    state_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        state,
    )

    chain.append_event(
        event_id="INITIAL-MONEY-STATE-002",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T06:00:02",
        payload={
            "currency": state["currency"],
            "balances": state["balances"],
            "state_hash": state_hash,
        },
        evidence={
            "type": "INITIAL_MONEY_COMMITMENT",
            "reference": "MONEY-COMMITMENT-002",
        },
    )

    stored_payload = (
        chain.entries[0]
        .event_payload
    )

    stored_payload["balances"]["BUYER"] = 900

    reconstructed_state = {
        "currency": stored_payload["currency"],
        "balances": stored_payload["balances"],
    }

    recalculated_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        reconstructed_state,
    )

    assert (
        recalculated_hash
        != stored_payload["state_hash"]
    )


def test_initial_money_state_currency_tampering_is_detected():

    chain = make_chain()
    state = make_initial_money_state()

    state_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        state,
    )

    chain.append_event(
        event_id="INITIAL-MONEY-STATE-003",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T06:00:03",
        payload={
            "currency": state["currency"],
            "balances": state["balances"],
            "state_hash": state_hash,
        },
        evidence={
            "type": "INITIAL_MONEY_COMMITMENT",
            "reference": "MONEY-COMMITMENT-003",
        },
    )

    stored_payload = (
        chain.entries[0]
        .event_payload
    )

    stored_payload["currency"] = "USD"

    reconstructed_state = {
        "currency": stored_payload["currency"],
        "balances": stored_payload["balances"],
    }

    recalculated_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        reconstructed_state,
    )

    assert (
        recalculated_hash
        != stored_payload["state_hash"]
    )