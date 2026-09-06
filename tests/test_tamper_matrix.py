import inspect
import json
from dataclasses import replace

import pytest

from core.canonical import canonical_bytes
from witness.chain import WitnessChain
from persistence.serializer import serialize_chain
from verifier.independent_verifier import IndependentVerifier
from verifier import independent_verifier


@pytest.fixture
def base_chain():
    chain = WitnessChain(
        initial_state={
            "initialized": False,
            "sequence_counter": 0,
        },
        manifest={
            "project": "V76-Lock",
            "version": "0",
        },
        witness_id="witness-core-01",
    )

    chain.append_event(
        event_id="EVT-001",
        event_type="INIT_STATE",
        timestamp="2026-03-30T00:00:00Z",
        payload={"value": 100},
        evidence={"doc": "auth-1"},
    )

    chain.append_event(
        event_id="EVT-002",
        event_type="UPDATE_STATE",
        timestamp="2026-03-30T01:00:00Z",
        payload={"value": 200},
        evidence={"doc": "auth-2"},
    )

    return chain


def test_valid_baseline(base_chain):
    data = serialize_chain(base_chain)

    assert IndependentVerifier().verify_bytes(data) is True


def test_tamper_A_event(base_chain):
    base_chain.entries[1].event_payload["value"] = 999

    data = serialize_chain(base_chain)

    assert IndependentVerifier().verify_bytes(data) is False


def test_tamper_B_state(base_chain):
    old_rec = base_chain.entries[0].record

    base_chain.entries[0].record = replace(
        old_rec,
        new_state_hash="fake_state_hash",
    )

    data = serialize_chain(base_chain)

    assert IndependentVerifier().verify_bytes(data) is False


def test_tamper_C_evidence(base_chain):
    base_chain.entries[0].evidence["doc"] = "forged-doc"

    data = serialize_chain(base_chain)

    assert IndependentVerifier().verify_bytes(data) is False


def test_tamper_D_sequence(base_chain):
    old_rec = base_chain.entries[1].record

    base_chain.entries[1].record = replace(
        old_rec,
        sequence=50,
    )

    data = serialize_chain(base_chain)

    assert IndependentVerifier().verify_bytes(data) is False


def test_tamper_E_manifest(base_chain):
    raw_bytes = serialize_chain(base_chain)

    bundle = json.loads(
        raw_bytes.decode("utf-8")
    )

    bundle["manifest"]["version"] = "999.0"

    tampered_bytes = canonical_bytes(bundle)

    assert IndependentVerifier().verify_bytes(
        tampered_bytes
    ) is False


def test_tamper_F_replay(base_chain):
    duplicate_entry = base_chain.entries[0]

    base_chain.entries.append(
        duplicate_entry
    )

    data = serialize_chain(base_chain)

    assert IndependentVerifier().verify_bytes(data) is False


def test_tamper_G_fork():
    chain1 = WitnessChain(
        {"initialized": False},
        {"project": "V76-Lock"},
        "w-01",
    )

    chain1.append_event(
        "E1",
        "INIT_STATE",
        "2026-03-30T00:00:00Z",
        {"v": 10},
        {"d": "1"},
    )

    chain2 = WitnessChain(
        {"initialized": False},
        {"project": "V76-Lock"},
        "w-01",
    )

    chain2.append_event(
        "E1",
        "INIT_STATE",
        "2026-03-30T00:00:00Z",
        {"v": 999},
        {"d": "1"},
    )

    bundle1 = json.loads(
        serialize_chain(chain1).decode("utf-8")
    )

    bundle2 = json.loads(
        serialize_chain(chain2).decode("utf-8")
    )

    assert IndependentVerifier().verify_no_fork(
        [bundle1, bundle2]
    ) is False


def test_tamper_H_serialization_bytes(base_chain):
    raw_bytes = serialize_chain(base_chain)

    bundle = json.loads(
        raw_bytes.decode("utf-8")
    )

    bundle["entries"][0]["event_payload"]["value"] = 999

    tampered_bytes = canonical_bytes(bundle)

    assert IndependentVerifier().verify_bytes(
        tampered_bytes
    ) is False


def test_independent_verifier_zero_coupling():
    source = inspect.getsource(
        independent_verifier
    )

    assert "WitnessChain" not in source
    assert "witness.chain" not in source


def test_disk_round_trip(base_chain):
    data = serialize_chain(base_chain)

    reloaded_bytes = bytes(data)

    assert IndependentVerifier().verify_bytes(
        reloaded_bytes
    ) is True