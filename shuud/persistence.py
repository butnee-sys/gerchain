"""Durable SHUUD state persistence adapter.

This module persists a verification-first SHUUD bundle as JSON in SQLite.
It deliberately stores the authoritative WitnessChain bundle and reconstructs
it through WitnessChain.from_dict(), so persisted witness data is never
trusted without cryptographic/state verification.

The adapter is intentionally separate from the FastAPI registry wiring. This
keeps the current sandbox API behavior unchanged until the persistence layer
has its own regression coverage.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from sqlalchemy import Column, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from witness.chain import WitnessChain


Base = declarative_base()


class SHUUDStateRow(Base):
    """One durable, recoverable SHUUD state snapshot per incident."""

    __tablename__ = "shuud_state"

    incident_id = Column(String, primary_key=True)
    snapshot_json = Column(Text, nullable=False)


class SHUUDPersistence:
    """SQLite-backed SHUUD persistence with verification-first recovery."""

    def __init__(self, database_url: str = "sqlite:///./gerchain.db") -> None:
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, connect_args=connect_args)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    @staticmethod
    def _canonical_snapshot(snapshot: Dict[str, Any]) -> str:
        return json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def save_snapshot(self, incident_id: str, snapshot: Dict[str, Any]) -> None:
        if not incident_id or not incident_id.strip():
            raise ValueError("incident_id is required")
        if not isinstance(snapshot, dict):
            raise ValueError("snapshot must be a dictionary")

        encoded = self._canonical_snapshot(snapshot)
        with self.SessionLocal() as session:
            row = session.get(SHUUDStateRow, incident_id)
            if row is None:
                row = SHUUDStateRow(incident_id=incident_id, snapshot_json=encoded)
                session.add(row)
            else:
                row.snapshot_json = encoded
            session.commit()

    def load_snapshot(self, incident_id: str) -> Dict[str, Any] | None:
        with self.SessionLocal() as session:
            row = session.get(SHUUDStateRow, incident_id)
            if row is None:
                return None
            value = json.loads(row.snapshot_json)
            if not isinstance(value, dict):
                raise ValueError("persisted SHUUD snapshot must be a dictionary")
            return value

    def delete_snapshot(self, incident_id: str) -> None:
        with self.SessionLocal() as session:
            row = session.get(SHUUDStateRow, incident_id)
            if row is not None:
                session.delete(row)
                session.commit()

    def recover_witness(self, incident_id: str) -> WitnessChain:
        snapshot = self.load_snapshot(incident_id)
        if snapshot is None:
            raise KeyError(f"SHUUD snapshot not found: {incident_id}")

        bundle = snapshot.get("witness_bundle")
        if not isinstance(bundle, dict):
            raise ValueError("persisted SHUUD snapshot is missing witness_bundle")

        # Verification-first recovery. WitnessChain.from_dict() recalculates
        # manifest/event/evidence/state hashes and rejects tampering.
        return WitnessChain.from_dict(bundle)


__all__ = ["SHUUDPersistence", "SHUUDStateRow", "Base"]
