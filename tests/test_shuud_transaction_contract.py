"""SH-16.16 transaction contract tests for durable settlement."""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from shuud.persistence import (
    SHUUDPersistenceBase,
    SHUUDReleaseAuthorizationRecord,
    SHUUDEscrowRecord,
    SHUUDLifecycleEvent,
    atomic_settlement,
)
from tests.test_shuud_production_wiring import _publication


def _engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'transaction.db'}", future=True)
    SHUUDPersistenceBase.metadata.create_all(engine)
    return engine


def test_duplicate_authorization_rolls_back_entire_settlement(tmp_path):
    engine = _engine(tmp_path)
    publication = _publication()
    atomic_settlement(engine, **publication.__dict__)

    conflicting = _publication()
    conflicting.authorization["authorization_hash"] = "AUTH-CONFLICT" if isinstance(conflicting.authorization, dict) else conflicting.authorization

    # Reuse the exact incident/authorization identity but change the escrow
    # projection; the unique authorization row must reject the whole transaction.
    with pytest.raises(IntegrityError):
        atomic_settlement(
            engine,
            lifecycle_event={**publication.lifecycle_event, "event_id": "EV-CONFLICT", "event_hash": "HASH-CONFLICT"},
            authorization=publication.authorization,
            escrow={**publication.escrow, "amount_nef": "999999"},
        )

    with Session(engine) as session:
        assert len(session.scalars(select(SHUUDEscrowRecord)).all()) == 1
        assert len(session.scalars(select(SHUUDLifecycleEvent)).all()) == 1
        assert len(session.scalars(select(SHUUDReleaseAuthorizationRecord)).all()) == 1


def test_amount_mismatch_fails_before_database_write(tmp_path):
    engine = _engine(tmp_path)
    publication = _publication()
    with pytest.raises(ValueError, match="amount"):
        atomic_settlement(
            engine,
            lifecycle_event=publication.lifecycle_event,
            authorization=publication.authorization,
            escrow={**publication.escrow, "amount_nef": "1500001"},
        )

    with Session(engine) as session:
        assert session.scalar(select(SHUUDEscrowRecord)) is None
        assert session.scalar(select(SHUUDReleaseAuthorizationRecord)) is None
        assert session.scalar(select(SHUUDLifecycleEvent)) is None
