"""
GerChain V83.2
Authorized Multi-Node Cryptographic Consensus Tests.

Purpose:
- V83 Authorization-ийг V82.1 Consensus-тэй шууд нэгтгэснийг шалгах.
- Зөвшөөрөгдсөн + хүчинтэй node consensus-д оролцох.
- Зөвшөөрөгдөөгүй node автоматаар хасагдах.
- Зөвшөөрөгдсөн боловч эвдэрсэн bundle хасагдах.
- Authorization нь криптографийн шалгалтыг орлохгүй байх.
- Cryptographic validity нь authorization-ийг орлохгүй байх.
- Quorum зөвхөн authorized + verified node дээр тооцогдох.
"""

from __future__ import annotations

import copy
import json

import pytest

from core.hashing import domain_hash
from network.authorization import (
    AuthorizedWitnessRegistry,
)
from network.consensus import (
    MultiNodeConsensus,
)
from persistence.serializer import (
    serialize_chain,
)
from witness.chain import WitnessChain


def build_bundle(
    witness_id: str,
    buyer_balance: int = 1000,
):
    """
    V83.2 тестийн хүчинтэй Witness Bundle.
    """

    money_state = {
        "currency": "MNT",
        "balances": {
            "BUYER": buyer_balance,
            "SELLER": 0,
        },
    }

    chain = WitnessChain(
        initial_state={
            "value": 0,
            "sequence_counter": 0,
            "initialized": False,
        },
        manifest={
            "system": "GerChain",
            "version": "V83.2",
            "purpose": "Authorized Consensus",
        },
        witness_id=witness_id,
        initial_money_state=money_state,
    )

    state_hash = domain_hash(
        "INITIAL_MONEY_STATE",
        money_state,
    )

    chain.append_event(
        event_id="V832-INITIAL-MONEY-001",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T17:00:01",
        payload={
            "state": money_state,
            "state_hash": state_hash,
        },
        evidence={
            "type": "INITIAL_MONEY_COMMITMENT",
            "reference": "V832-001",
        },
    )

    return json.loads(
        serialize_chain(
            chain
        ).decode("utf-8")
    )


def test_consensus_accepts_authorized_valid_node():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    consensus = MultiNodeConsensus(
        quorum=1,
        authorization_registry=registry,
    )

    bundle = build_bundle(
        "NODE-A"
    )

    result = consensus.verify_node_bundle(
        "NODE-A",
        bundle,
    )

    assert result["authorized"] is True
    assert result["verified"] is True
    assert result["status"] == "VALID"
    assert result["chain_tip"] is not None


def test_consensus_rejects_unauthorized_node():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    consensus = MultiNodeConsensus(
        quorum=1,
        authorization_registry=registry,
    )

    bundle = build_bundle(
        "NODE-X"
    )

    result = consensus.verify_node_bundle(
        "NODE-X",
        bundle,
    )

    assert result["authorized"] is False
    assert result["verified"] is False
    assert result["status"] == "UNAUTHORIZED"
    assert result["chain_tip"] is None


def test_unauthorized_node_with_valid_bundle_is_not_consensus_eligible():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    consensus = MultiNodeConsensus(
        quorum=2,
        authorization_registry=registry,
    )

    valid_bundle = build_bundle(
        "NODE-X"
    )

    report = consensus.verify_network(
        {
            "NODE-X": valid_bundle,
        }
    )

    assert report["node_count"] == 1
    assert report["authorized_node_count"] == 0
    assert report["verified_node_count"] == 0
    assert report["authorized_verified_count"] == 0

    assert (
        report["consensus"]
        == "NO_AUTHORIZED_VALID_NODES"
    )

    assert report["chain_tip"] is None
    assert report["consensus_count"] == 0


def test_authorized_two_of_three_nodes_reach_quorum():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
            "NODE-C",
        ]
    )

    consensus = MultiNodeConsensus(
        quorum=2,
        authorization_registry=registry,
    )

    bundle = build_bundle(
        "NODE-A"
    )

    report = consensus.verify_network(
        {
            "NODE-A": copy.deepcopy(bundle),
            "NODE-B": copy.deepcopy(bundle),
            "NODE-C": copy.deepcopy(bundle),
        }
    )

    assert report["node_count"] == 3
    assert report["authorized_node_count"] == 3
    assert report["verified_node_count"] == 3
    assert report["authorized_verified_count"] == 3

    assert (
        report["consensus"]
        == "QUORUM_REACHED"
    )

    assert report["consensus_count"] == 3

    assert sorted(
        report["consensus_nodes"]
    ) == [
        "NODE-A",
        "NODE-B",
        "NODE-C",
    ]


def test_unauthorized_node_does_not_count_toward_quorum():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    consensus = MultiNodeConsensus(
        quorum=2,
        authorization_registry=registry,
    )

    bundle = build_bundle(
        "NODE-A"
    )

    report = consensus.verify_network(
        {
            "NODE-A": copy.deepcopy(bundle),
            "NODE-B": copy.deepcopy(bundle),
            "NODE-X": copy.deepcopy(bundle),
        }
    )

    assert report["node_count"] == 3
    assert report["authorized_node_count"] == 2
    assert report["verified_node_count"] == 2
    assert report["authorized_verified_count"] == 2

    assert (
        report["consensus"]
        == "QUORUM_REACHED"
    )

    assert report["consensus_count"] == 2

    assert sorted(
        report["consensus_nodes"]
    ) == [
        "NODE-A",
        "NODE-B",
    ]


def test_authorized_but_tampered_bundle_is_rejected():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    consensus = MultiNodeConsensus(
        quorum=1,
        authorization_registry=registry,
    )

    bundle = build_bundle(
        "NODE-A"
    )

    tampered = copy.deepcopy(
        bundle
    )

    tampered[
        "manifest_hash"
    ] = "0" * 64

    result = consensus.verify_node_bundle(
        "NODE-A",
        tampered,
    )

    assert result["authorized"] is True
    assert result["verified"] is False
    assert result["status"] == "INVALID_BUNDLE"
    assert result["chain_tip"] is None


def test_authorized_invalid_node_does_not_reach_quorum():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    consensus = MultiNodeConsensus(
        quorum=2,
        authorization_registry=registry,
    )

    valid_bundle = build_bundle(
        "NODE-A"
    )

    invalid_bundle = copy.deepcopy(
        valid_bundle
    )

    invalid_bundle[
        "manifest_hash"
    ] = "0" * 64

    report = consensus.verify_network(
        {
            "NODE-A": valid_bundle,
            "NODE-B": invalid_bundle,
        }
    )

    assert report["authorized_node_count"] == 2
    assert report["verified_node_count"] == 1
    assert report["authorized_verified_count"] == 1

    assert (
        report["consensus"]
        == "QUORUM_NOT_REACHED"
    )

    assert report["consensus_count"] == 0
    assert report["chain_tip"] is None


def test_authorization_is_checked_before_cryptographic_verification():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    consensus = MultiNodeConsensus(
        quorum=1,
        authorization_registry=registry,
    )

    invalid_bundle = {
        "completely": "invalid",
    }

    result = consensus.verify_node_bundle(
        "NODE-X",
        invalid_bundle,
    )

    assert result["authorized"] is False
    assert result["verified"] is False
    assert result["status"] == "UNAUTHORIZED"


def test_cryptographic_verification_is_still_required_after_authorization():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    consensus = MultiNodeConsensus(
        quorum=1,
        authorization_registry=registry,
    )

    invalid_bundle = {
        "manifest": {},
        "manifest_hash": "0" * 64,
        "witness_id": "NODE-A",
        "initial_state": {},
        "entries": [],
    }

    result = consensus.verify_node_bundle(
        "NODE-A",
        invalid_bundle,
    )

    assert result["authorized"] is True
    assert result["verified"] is False
    assert result["chain_tip"] is None


def test_different_authorized_chain_tips_produce_split_consensus():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    consensus = MultiNodeConsensus(
        quorum=2,
        authorization_registry=registry,
    )

    bundle_a = build_bundle(
        "NODE-A",
        buyer_balance=1000,
    )

    bundle_b = build_bundle(
        "NODE-B",
        buyer_balance=900,
    )

    report = consensus.verify_network(
        {
            "NODE-A": bundle_a,
            "NODE-B": bundle_b,
        }
    )

    assert report["authorized_node_count"] == 2
    assert report["verified_node_count"] == 2
    assert report["authorized_verified_count"] == 2

    assert (
        report["consensus"]
        == "SPLIT_CONSENSUS"
    )

    assert report["chain_tip"] is None
    assert report["consensus_count"] == 0


def test_revoked_node_is_automatically_excluded():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    consensus = MultiNodeConsensus(
        quorum=2,
        authorization_registry=registry,
    )

    bundle = build_bundle(
        "NODE-A"
    )

    registry.remove(
        "NODE-B"
    )

    report = consensus.verify_network(
        {
            "NODE-A": copy.deepcopy(bundle),
            "NODE-B": copy.deepcopy(bundle),
        }
    )

    assert report["authorized_node_count"] == 1
    assert report["verified_node_count"] == 1
    assert report["authorized_verified_count"] == 1

    assert (
        report["consensus"]
        == "QUORUM_NOT_REACHED"
    )

    assert report["consensus_count"] == 0


def test_reauthorized_node_can_participate_again():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    consensus = MultiNodeConsensus(
        quorum=1,
        authorization_registry=registry,
    )

    bundle = build_bundle(
        "NODE-A"
    )

    registry.remove(
        "NODE-A"
    )

    revoked = consensus.verify_node_bundle(
        "NODE-A",
        bundle,
    )

    assert revoked["status"] == "UNAUTHORIZED"

    registry.add(
        "NODE-A"
    )

    restored = consensus.verify_node_bundle(
        "NODE-A",
        bundle,
    )

    assert restored["authorized"] is True
    assert restored["verified"] is True
    assert restored["status"] == "VALID"


def test_chain_tip_is_unchanged_by_authorization_layer():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    bundle = build_bundle(
        "NODE-A"
    )

    crypto_only = MultiNodeConsensus(
        quorum=1
    )

    authorized = MultiNodeConsensus(
        quorum=1,
        authorization_registry=registry,
    )

    tip_without_authorization = (
        crypto_only.compute_chain_tip(
            bundle
        )
    )

    tip_with_authorization = (
        authorized.compute_chain_tip(
            bundle
        )
    )

    assert (
        tip_without_authorization
        == tip_with_authorization
    )


def test_chain_tip_is_not_computed_for_unauthorized_node():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    consensus = MultiNodeConsensus(
        quorum=1,
        authorization_registry=registry,
    )

    bundle = build_bundle(
        "NODE-X"
    )

    result = consensus.verify_node_bundle(
        "NODE-X",
        bundle,
    )

    assert result["status"] == "UNAUTHORIZED"
    assert result["chain_tip"] is None


def test_status_reports_authorized_nodes():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-C",
            "NODE-A",
            "NODE-B",
        ]
    )

    consensus = MultiNodeConsensus(
        quorum=2,
        authorization_registry=registry,
    )

    status = consensus.status()

    assert status["version"] == "V83.2"
    assert status["quorum"] == 2

    assert status[
        "authorized_nodes"
    ] == [
        "NODE-A",
        "NODE-B",
        "NODE-C",
    ]

    assert status[
        "authorized_count"
    ] == 3


def test_no_authorized_valid_nodes_returns_explicit_status():
    registry = AuthorizedWitnessRegistry()

    consensus = MultiNodeConsensus(
        quorum=1,
        authorization_registry=registry,
    )

    bundle = build_bundle(
        "NODE-X"
    )

    report = consensus.verify_network(
        {
            "NODE-X": bundle,
        }
    )

    assert report[
        "authorized_node_count"
    ] == 0

    assert report[
        "authorized_verified_count"
    ] == 0

    assert (
        report["consensus"]
        == "NO_AUTHORIZED_VALID_NODES"
    )

    assert report["chain_tip"] is None