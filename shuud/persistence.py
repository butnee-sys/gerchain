"""Durable SHUUD state persistence adapter.

This adapter stores a canonical SHUUD state snapshot and recovers its
authoritative WitnessChain only through verification-first reconstruction.
It does not replace GerChain WitnessChain or EscrowEngine.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import Column, String, Text, create_engine, update
from sqlalchemy.orm import declarative_base, sessionmaker

from witness.chain import WitnessChain


Base = declarative_base()


class SHUUDStateRow(Base):
    __tablename__ = "shuud_state"

    incident_id = Column(String, primary_key=True)
    snapshot_json = Column(Text, nullable=False)


class SHUUDSandboxConfigRow(Base):
    __tablename__ = "shuud_sandbox_config"

    sandbox_id = Column(String, primary_key=True)
    config_json = Column(Text, nullable=False)


class SHUUDPersistence:
    """Durable SHUUD persistence with verification-first recovery."""

    def __init__(self, database_url: str = "sqlite:///./gerchain.db") -> None:
        connect_args = (
            {"check_same_thread": False}
            if database_url.startswith("sqlite")
            else {}
        )
        self.engine = create_engine(database_url, connect_args=connect_args)
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        Base.metadata.create_all(bind=self.engine)

    @staticmethod
    def _canonical_snapshot(snapshot: dict[str, Any]) -> str:
        return json.dumps(
            snapshot,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def save_snapshot(self, incident_id: str, snapshot: dict[str, Any]) -> None:
        if not incident_id or not incident_id.strip():
            raise ValueError("incident_id is required")
        if not isinstance(snapshot, dict):
            raise ValueError("snapshot must be a dictionary")

        encoded = self._canonical_snapshot(snapshot)
        with self.SessionLocal() as session:
            row = session.get(SHUUDStateRow, incident_id)
            if row is None:
                row = SHUUDStateRow(
                    incident_id=incident_id,
                    snapshot_json=encoded,
                )
                session.add(row)
            else:
                row.snapshot_json = encoded
            session.commit()

    def save_snapshot_if_current(
        self,
        incident_id: str,
        expected_snapshot: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> bool:
        """Atomically replace a snapshot only when it still matches expected."""
        if not incident_id or not incident_id.strip():
            raise ValueError("incident_id is required")
        if not isinstance(expected_snapshot, dict):
            raise ValueError("expected_snapshot must be a dictionary")
        if not isinstance(snapshot, dict):
            raise ValueError("snapshot must be a dictionary")

        expected_encoded = self._canonical_snapshot(expected_snapshot)
        encoded = self._canonical_snapshot(snapshot)

        with self.SessionLocal() as session:
            result = session.execute(
                update(SHUUDStateRow)
                .where(
                    SHUUDStateRow.incident_id == incident_id,
                    SHUUDStateRow.snapshot_json == expected_encoded,
                )
                .values(snapshot_json=encoded)
            )
            if result.rowcount != 1:
                session.rollback()
                return False

            session.commit()
            return True

    def save_economic_measurement_if_current(
        self,
        incident_id: str,
        expected_snapshot: dict[str, Any],
        economic_measurement: dict[str, Any],
    ) -> bool:
        """Atomically persist an economic measurement on the canonical snapshot."""
        if not isinstance(economic_measurement, dict):
            raise ValueError("economic_measurement must be a dictionary")

        updated = dict(expected_snapshot)
        updated["economic_measurement"] = dict(economic_measurement)
        return self.save_snapshot_if_current(incident_id, expected_snapshot, updated)

    def load_snapshot(self, incident_id: str) -> dict[str, Any] | None:
        with self.SessionLocal() as session:
            row = session.get(SHUUDStateRow, incident_id)
            if row is None:
                return None
            value = json.loads(row.snapshot_json)
            if not isinstance(value, dict):
                raise ValueError(
                    "persisted SHUUD snapshot must be a dictionary"
                )
            return value

    def save_sandbox_config(self, sandbox_id: str, config: dict[str, Any]) -> None:
        """Create or replace the durable Day-0 sandbox configuration."""
        if not sandbox_id or not sandbox_id.strip():
            raise ValueError("sandbox_id is required")
        if not isinstance(config, dict):
            raise ValueError("config must be a dictionary")

        encoded = self._canonical_snapshot(config)
        with self.SessionLocal() as session:
            row = session.get(SHUUDSandboxConfigRow, sandbox_id)
            if row is None:
                row = SHUUDSandboxConfigRow(
                    sandbox_id=sandbox_id,
                    config_json=encoded,
                )
                session.add(row)
            else:
                row.config_json = encoded
            session.commit()

    def load_sandbox_config(self, sandbox_id: str) -> dict[str, Any] | None:
        with self.SessionLocal() as session:
            row = session.get(SHUUDSandboxConfigRow, sandbox_id)
            if row is None:
                return None
            value = json.loads(row.config_json)
            if not isinstance(value, dict):
                raise ValueError(
                    "persisted SHUUD sandbox config must be a dictionary"
                )
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
            raise ValueError(
                "persisted SHUUD snapshot is missing witness_bundle"
            )

        return WitnessChain.from_dict(bundle)


__all__ = [
    "SHUUDPersistence",
    "SHUUDSandboxConfigRow",
    "SHUUDStateRow",
    "Base",
]
