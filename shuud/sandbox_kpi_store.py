"""Durable session-level SHUUD sandbox KPI records.

Measurement storage only. It does not own incident, witness, escrow, or settlement state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import median
from typing import Any

from sqlalchemy import Column, Float, String, create_engine, select
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class SHUUDSandboxKpiRow(Base):
    __tablename__ = "shuud_sandbox_kpi"

    incident_id = Column(String, primary_key=True)
    recorded_at = Column(String, nullable=False)
    clearance_seconds = Column(Float, nullable=False)
    within_two_minutes = Column(String, nullable=False)
    shiid_approved = Column(String, nullable=False)
    release_succeeded = Column(String, nullable=False)
    total_savings_mnt = Column(Float, nullable=False)


@dataclass(frozen=True)
class SandboxKpiRecord:
    incident_id: str
    recorded_at: str
    clearance_seconds: float
    within_two_minutes: bool
    shiid_approved: bool
    release_succeeded: bool
    total_savings_mnt: float


class SHUUDSandboxKpiStore:
    """Durable KPI records with simple aggregate queries."""

    def __init__(self, database_url: str) -> None:
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, connect_args=connect_args)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    @staticmethod
    def _bool(value: Any) -> str:
        return "1" if bool(value) else "0"

    def record(self, record: SandboxKpiRecord) -> None:
        with self.SessionLocal() as session:
            row = session.get(SHUUDSandboxKpiRow, record.incident_id)
            payload = {
                "recorded_at": record.recorded_at,
                "clearance_seconds": record.clearance_seconds,
                "within_two_minutes": self._bool(record.within_two_minutes),
                "shiid_approved": self._bool(record.shiid_approved),
                "release_succeeded": self._bool(record.release_succeeded),
                "total_savings_mnt": record.total_savings_mnt,
            }
            if row is None:
                session.add(SHUUDSandboxKpiRow(incident_id=record.incident_id, **payload))
            else:
                for key, value in payload.items():
                    setattr(row, key, value)
            session.commit()

    def aggregate(self, start_at: datetime | None = None) -> dict[str, Any]:
        with self.SessionLocal() as session:
            stmt = select(SHUUDSandboxKpiRow).order_by(SHUUDSandboxKpiRow.recorded_at.asc())
            rows = list(session.execute(stmt).scalars())

        if start_at is not None:
            start_iso = start_at.astimezone(timezone.utc).isoformat()
            rows = [row for row in rows if row.recorded_at >= start_iso]

        clearances = [float(row.clearance_seconds) for row in rows]
        total = len(rows)
        within = sum(row.within_two_minutes == "1" for row in rows)
        approved = sum(row.shiid_approved == "1" for row in rows)
        released = sum(row.release_succeeded == "1" for row in rows)
        savings = sum(float(row.total_savings_mnt) for row in rows)

        return {
            "status": "success",
            "scope": "sandbox_backend",
            "total_cases": total,
            "within_two_minutes_cases": within,
            "within_two_minutes_rate": (within / total) if total else 0.0,
            "shiid_approved_cases": approved,
            "shiid_approval_rate": (approved / total) if total else 0.0,
            "release_success_cases": released,
            "release_success_rate": (released / total) if total else 0.0,
            "average_clearance_seconds": (sum(clearances) / total) if total else None,
            "median_clearance_seconds": median(clearances) if clearances else None,
            "total_savings_mnt": savings,
            "first_recorded_at": rows[0].recorded_at if rows else None,
            "last_recorded_at": rows[-1].recorded_at if rows else None,
        }


__all__ = ["SandboxKpiRecord", "SHUUDSandboxKpiStore", "SHUUDSandboxKpiRow", "Base"]
