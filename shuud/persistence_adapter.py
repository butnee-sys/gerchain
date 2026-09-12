"""Persistence adapter boundary for SHUUD settlement publication.

The domain layer depends on this small contract rather than on SQLAlchemy.
Sandbox and production may provide different implementations without changing
WitnessChain, EscrowEngine, or IndependentVerifier authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SettlementPublication:
    lifecycle_event: dict
    authorization: dict
    escrow: dict


class SettlementPersistence(Protocol):
    """Durable publication contract; implementations own transaction scope."""

    def publish_settlement(self, publication: SettlementPublication) -> None:
        ...


class MemorySettlementPersistence:
    """Explicit sandbox adapter; not suitable for production settlement."""

    def __init__(self) -> None:
        self.publications: list[SettlementPublication] = []

    def publish_settlement(self, publication: SettlementPublication) -> None:
        self.publications.append(publication)


class SQLAlchemySettlementPersistence:
    """Durable adapter backed by the SHUUD SQLAlchemy transaction boundary."""

    def __init__(self, engine) -> None:
        self.engine = engine

    def publish_settlement(self, publication: SettlementPublication) -> None:
        from .persistence import atomic_settlement

        atomic_settlement(
            self.engine,
            lifecycle_event=publication.lifecycle_event,
            authorization=publication.authorization,
            escrow=publication.escrow,
        )


__all__ = [
    "SettlementPublication",
    "SettlementPersistence",
    "MemorySettlementPersistence",
    "SQLAlchemySettlementPersistence",
]
