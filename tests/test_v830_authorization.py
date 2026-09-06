"""
GerChain V83.0
Authorized Witness Node Registry Tests.

Purpose:
- Зөвшөөрөгдсөн node бүртгэх.
- Зөвшөөрөгдсөн node-ийг таних.
- Зөвшөөрөгдөөгүй node-ийг таних.
- Давхардсан node бүртгэлийг хориглох.
- Зөвшөөрлийг цуцлах.
- Олон node-ийн эрхийг зэрэг шалгах.
- Буруу node_id төрлийг зөв барих.
- Registry-ийн төлөвийг тогтвортой буцаах.
"""

from __future__ import annotations

import pytest

from network.authorization import (
    AuthorizedWitnessRegistry,
)


def test_empty_registry_has_zero_nodes():
    registry = AuthorizedWitnessRegistry()

    assert registry.count() == 0
    assert registry.node_ids() == []

    status = registry.status()

    assert status["version"] == "V83.0"
    assert status["authorized_count"] == 0
    assert status["authorized_nodes"] == []


def test_add_authorized_node():
    registry = AuthorizedWitnessRegistry()

    registry.add("NODE-A")

    assert registry.count() == 1
    assert registry.is_authorized("NODE-A")
    assert registry.node_ids() == ["NODE-A"]


def test_multiple_nodes_are_authorized():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
            "NODE-C",
        ]
    )

    assert registry.count() == 3

    assert registry.is_authorized("NODE-A")
    assert registry.is_authorized("NODE-B")
    assert registry.is_authorized("NODE-C")

    assert registry.node_ids() == [
        "NODE-A",
        "NODE-B",
        "NODE-C",
    ]


def test_unauthorized_node_is_rejected():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    assert registry.is_authorized("NODE-A")
    assert registry.is_authorized("NODE-B")

    assert not registry.is_authorized(
        "NODE-X"
    )


def test_duplicate_node_is_rejected():
    registry = AuthorizedWitnessRegistry()

    registry.add("NODE-A")

    with pytest.raises(ValueError):
        registry.add("NODE-A")

    assert registry.count() == 1


def test_remove_authorized_node():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    assert registry.is_authorized(
        "NODE-A"
    )

    registry.remove("NODE-A")

    assert not registry.is_authorized(
        "NODE-A"
    )

    assert registry.is_authorized(
        "NODE-B"
    )

    assert registry.count() == 1


def test_remove_unknown_node_is_rejected():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    with pytest.raises(ValueError):
        registry.remove("NODE-X")

    assert registry.count() == 1
    assert registry.is_authorized(
        "NODE-A"
    )


def test_verify_authorized_node():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    result = registry.verify_node(
        "NODE-A"
    )

    assert result == {
        "version": "V83.0",
        "node_id": "NODE-A",
        "authorized": True,
    }


def test_verify_unauthorized_node():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    result = registry.verify_node(
        "NODE-X"
    )

    assert result == {
        "version": "V83.0",
        "node_id": "NODE-X",
        "authorized": False,
    }


def test_verify_multiple_nodes():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    result = registry.verify_nodes(
        [
            "NODE-A",
            "NODE-B",
            "NODE-X",
        ]
    )

    assert result[
        "authorized_count"
    ] == 2

    assert result[
        "unauthorized_count"
    ] == 1

    assert result[
        "authorized_nodes"
    ] == [
        "NODE-A",
        "NODE-B",
    ]

    assert result[
        "unauthorized_nodes"
    ] == [
        "NODE-X",
    ]

    assert result["results"] == {
        "NODE-A": True,
        "NODE-B": True,
        "NODE-X": False,
    }


def test_node_ids_are_sorted():
    registry = AuthorizedWitnessRegistry()

    registry.add("NODE-C")
    registry.add("NODE-A")
    registry.add("NODE-B")

    assert registry.node_ids() == [
        "NODE-A",
        "NODE-B",
        "NODE-C",
    ]


def test_registry_constructor_rejects_duplicate_nodes():
    with pytest.raises(ValueError):
        AuthorizedWitnessRegistry(
            [
                "NODE-A",
                "NODE-A",
            ]
        )


def test_empty_node_id_is_rejected():
    registry = AuthorizedWitnessRegistry()

    with pytest.raises(ValueError):
        registry.add("")


def test_non_string_node_id_is_rejected():
    registry = AuthorizedWitnessRegistry()

    with pytest.raises(TypeError):
        registry.add(123)


def test_is_authorized_rejects_invalid_types():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    assert not registry.is_authorized(
        123
    )

    assert not registry.is_authorized(
        None
    )

    assert not registry.is_authorized(
        ""
    )


def test_authorization_survives_independent_registry_instances():
    registry_a = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    registry_b = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    assert registry_a.node_ids() == (
        registry_b.node_ids()
    )

    assert registry_a.is_authorized(
        "NODE-A"
    )

    assert registry_b.is_authorized(
        "NODE-A"
    )


def test_removed_node_cannot_be_verified_as_authorized():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
            "NODE-B",
        ]
    )

    registry.remove("NODE-A")

    result = registry.verify_node(
        "NODE-A"
    )

    assert result["authorized"] is False
    assert registry.count() == 1


def test_reauthorization_after_removal():
    registry = AuthorizedWitnessRegistry(
        [
            "NODE-A",
        ]
    )

    registry.remove("NODE-A")

    assert not registry.is_authorized(
        "NODE-A"
    )

    registry.add("NODE-A")

    assert registry.is_authorized(
        "NODE-A"
    )

    assert registry.count() == 1