"""
GerChain V80.4.3
Independent Initial Money State Verification Tests.

Purpose:
- Initial Money State commitment-ийг семантик түвшинд шалгах.
- Төлөв өөрчлөгдсөн ч event hash-ийг дахин тооцсон
  тохиолдолд Independent Verifier REJECT хийх.
- Иймээс зөвхөн криптографийн event hash бус,
  Initial Money State-ийн утгын дүрэм ажиллаж байгааг батлах.
"""

import json

from core.hashing import domain_hash
from persistence.serializer import serialize_chain
from verifier.v80_independent_verifier import (
    V80IndependentVerifier,
)
from witness.chain import WitnessChain


def build_chain():

    initial_state = {
        "value": 0,
        "sequence_counter": 0,
        "initialized": False,
    }

    manifest = {
        "system": "GerChain",
        "version": "V80.4.3",
        "purpose": "Independent Initial Money Verification",
    }

    money_state = {
        "currency": "MNT",
        "balances": {
            "BUYER": 1000,
            "SELLER": 0,
        },
    }

    chain = WitnessChain(
        initial_state=initial_state,
        manifest=manifest,
        witness_id="WITNESS-INITIAL-MONEY-VERIFY-001",
        initial_money_state=money_state,
    )

    return chain


def add_initial_money_event(chain):

    commitment = (
        chain.get_initial_money_commitment()
    )

    chain.append_event(
        event_id="INITIAL-MONEY-VERIFY-001",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T07:00:01",
        payload={
            "state": commitment["state"],
            "state_hash": commitment["state_hash"],
        },
        evidence={
            "type": "INITIAL_MONEY_COMMITMENT",
            "reference": "INITIAL-MONEY-VERIFY-001",
        },
    )


def make_bundle():

    chain = build_chain()

    add_initial_money_event(chain)

    serialized = serialize_chain(chain)

    return json.loads(
        serialized.decode("utf-8")
    )


def recompute_event_hash(entry):

    record = entry["record"]

    event_obj = {
        "sequence": record["sequence"],
        "event_id": record["event_id"],
        "event_type": record["event_type"],
        "timestamp": record["timestamp"],
        "payload": entry["event_payload"],
    }

    return domain_hash(
        "WITNESS_EVENT",
        event_obj,
    )


def test_valid_initial_money_commitment_passes():

    bundle = make_bundle()

    verifier = V80IndependentVerifier()

    assert (
        verifier.verify_bundle(bundle)
        is True
    )


def test_tampered_initial_balance_is_rejected_semantically():

    bundle = make_bundle()

    entry = bundle["entries"][0]

    entry[
        "event_payload"
    ][
        "state"
    ][
        "balances"
    ][
        "BUYER"
    ] = 900

    # Tampered payload-д тохируулж event hash-ийг
    # дахин тооцно.
    #
    # Ингэснээр зөвхөн event hash хамгаалалт
    # тестийг PASS болгох боломжгүй.
    entry[
        "record"
    ][
        "event_hash"
    ] = recompute_event_hash(entry)

    verifier = V80IndependentVerifier()

    assert (
        verifier.verify_bundle(bundle)
        is False
    )


def test_tampered_initial_currency_is_rejected_semantically():

    bundle = make_bundle()

    entry = bundle["entries"][0]

    entry[
        "event_payload"
    ][
        "state"
    ][
        "currency"
    ] = "USD"

    entry[
        "record"
    ][
        "event_hash"
    ] = recompute_event_hash(entry)

    verifier = V80IndependentVerifier()

    assert (
        verifier.verify_bundle(bundle)
        is False
    )


def test_tampered_initial_state_hash_is_rejected():

    bundle = make_bundle()

    entry = bundle["entries"][0]

    entry[
        "event_payload"
    ][
        "state_hash"
    ] = "0" * 64

    entry[
        "record"
    ][
        "event_hash"
    ] = recompute_event_hash(entry)

    verifier = V80IndependentVerifier()

    assert (
        verifier.verify_bundle(bundle)
        is False
    )


def test_initial_money_hash_matches_state():

    bundle = make_bundle()

    entry = bundle["entries"][0]

    state = (
        entry[
            "event_payload"
        ][
            "state"
        ]
    )

    stored_hash = (
        entry[
            "event_payload"
        ][
            "state_hash"
        ]
    )

    assert (
        domain_hash(
            "INITIAL_MONEY_STATE",
            state,
        )
        == stored_hash
    )