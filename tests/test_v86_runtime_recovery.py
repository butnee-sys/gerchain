import json

import pytest

from persistence.serializer import serialize_chain
from services.gerchain_runtime import GerchainRuntime
from verifier.v80_independent_verifier import V80IndependentVerifier
from witness.chain import ChainEntry, WitnessChain
from witness.record import WitnessRecord


def make_runtime():
    return GerchainRuntime(
        escrow_id="ESCROW-RECOVERY-001",
        amount=1000,
        currency="MNT",
        witness_id="WITNESS-RECOVERY-001",
        initial_state={
            "escrow_id": "ESCROW-RECOVERY-001",
            "state": "CREATED",
            "amount": 1000,
            "currency": "MNT",
            "transition_counter": 0,
        },
        manifest={
            "runtime": "GerchainRuntime",
            "version": "1.0.0",
            "currency": "MNT",
            "escrow_id": "ESCROW-RECOVERY-001",
        },
        initial_money_state={
            "currency": "MNT",
            "balances": {
                "BUYER": 1000,
                "SELLER": 0,
            },
        },
    )


def decode(data):
    return json.loads(data.decode("utf-8"))


def test_runtime_recovery_round_trip():
    runtime = make_runtime()

    serialized = runtime.serialize()
    bundle = decode(serialized)

    recovered = WitnessChain.from_dict(bundle)

    assert recovered.manifest == runtime.witness_chain.manifest
    assert recovered.manifest_hash == runtime.witness_chain.manifest_hash
    assert recovered.witness_id == runtime.witness_chain.witness_id
    assert recovered.initial_state == runtime.witness_chain.initial_state
    assert recovered.current_state == runtime.witness_chain.current_state
    assert recovered.current_state_hash == runtime.witness_chain.current_state_hash
    assert len(recovered.entries) == len(runtime.witness_chain.entries)

    assert serialize_chain(recovered) == serialized

    verifier = V80IndependentVerifier()
    assert verifier.verify_bundle(
        decode(serialize_chain(recovered))
    )

def test_serialized_runtime_contains_authoritative_initial_money_event():
    runtime = make_runtime()

    bundle = decode(runtime.serialize())

    initial_money_entries = [
        entry
        for entry in bundle["entries"]
        if entry["record"]["event_type"]
        == "INITIAL_MONEY_STATE"
    ]

    assert len(initial_money_entries) == 1

    entry = initial_money_entries[0]

    assert entry["event_payload"]["state"] == {
        "currency": "MNT",
        "balances": {
            "BUYER": 1000,
            "SELLER": 0,
        },
    }


def test_runtime_serialization_is_canonical():
    runtime = make_runtime()

    first = runtime.serialize()
    second = runtime.serialize()

    assert first == second


def test_runtime_bundle_verifies_independently():
    runtime = make_runtime()

    assert runtime.verify() is True
    report = runtime.verify_report()

    assert report["overall"] is True

def test_witness_chain_can_be_reconstructed_from_serialized_bundle():
    runtime = make_runtime()

    serialized = runtime.serialize()
    bundle = decode(serialized)

    recovered = WitnessChain.from_dict(bundle)

    assert recovered.manifest == runtime.witness_chain.manifest
    assert recovered.manifest_hash == runtime.witness_chain.manifest_hash
    assert recovered.witness_id == runtime.witness_chain.witness_id
    assert recovered.initial_state == runtime.witness_chain.initial_state
    assert recovered.current_state == runtime.witness_chain.current_state
    assert recovered.current_state_hash == runtime.witness_chain.current_state_hash
    assert len(recovered.entries) == len(runtime.witness_chain.entries)

    assert serialize_chain(recovered) == serialized

    verifier = V80IndependentVerifier()
    assert verifier.verify_bundle(decode(serialize_chain(recovered)))


def test_recovery_rejects_tampered_event_payload():
    runtime = make_runtime()
    bundle = decode(runtime.serialize())

    bundle["entries"][0]["event_payload"]["state"]["currency"] = "USD"

    with pytest.raises(ValueError, match="event hash mismatch"):
        WitnessChain.from_dict(bundle)


def test_recovery_rejects_tampered_event_hash():
    runtime = make_runtime()
    bundle = decode(runtime.serialize())

    bundle["entries"][0]["record"]["event_hash"] = "0" * 64

    with pytest.raises(ValueError, match="event hash mismatch"):
        WitnessChain.from_dict(bundle)


def test_recovery_rejects_tampered_initial_money_state():
    runtime = make_runtime()
    bundle = decode(runtime.serialize())

    initial_money_entry = next(
        entry
        for entry in bundle["entries"]
        if entry["record"]["event_type"] == "INITIAL_MONEY_STATE"
    )

    initial_money_entry["event_payload"]["state"]["balances"]["BUYER"] = 999

    with pytest.raises(ValueError, match="event hash mismatch"):
        WitnessChain.from_dict(bundle)
