from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from core.idempotency import IdempotencyConflictError, IdempotencyEngine


class IdempotencyBase(DeclarativeBase):
    pass


class IdempotencyRecordModel(IdempotencyBase):
    __tablename__ = "gerchain_idempotency_records"
    __table_args__ = (UniqueConstraint("operation", "idempotency_key", name="uq_gerchain_idempotency_operation_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="PROCESSING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


@dataclass(frozen=True)
class IdempotencyReplay:
    result: Any


class PostgreSQLIdempotencyStore:
    """DB-backed idempotency boundary for concurrent workers."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    @staticmethod
    def fingerprint(payload: Mapping[str, Any]) -> str:
        return IdempotencyEngine.fingerprint(payload)

    def begin(self, operation: str, key: str, payload: Mapping[str, Any]) -> IdempotencyReplay | None:
        if not operation or not key:
            raise ValueError("operation and idempotency key are required")
        fingerprint = self.fingerprint(payload)
        with self.session_factory() as session:
            row = session.execute(
                select(IdempotencyRecordModel)
                .where(IdempotencyRecordModel.operation == operation, IdempotencyRecordModel.idempotency_key == key)
                .with_for_update()
            ).scalar_one_or_none()
            if row is None:
                now = datetime.now(timezone.utc)
                row = IdempotencyRecordModel(operation=operation, idempotency_key=key, request_fingerprint=fingerprint, state="PROCESSING", created_at=now, updated_at=now)
                session.add(row)
                session.commit()
                return None
            if row.request_fingerprint != fingerprint:
                raise IdempotencyConflictError(f"idempotency key conflict: {operation}:{key}")
            if row.state == "COMPLETED":
                return IdempotencyReplay(_decode_result(row.result_json))
            raise RuntimeError(f"idempotency operation already processing: {operation}:{key}")

    def complete(self, operation: str, key: str, payload: Mapping[str, Any], result: Any) -> Any:
        fingerprint = self.fingerprint(payload)
        with self.session_factory() as session:
            row = session.execute(
                select(IdempotencyRecordModel)
                .where(IdempotencyRecordModel.operation == operation, IdempotencyRecordModel.idempotency_key == key)
                .with_for_update()
            ).scalar_one()
            if row.request_fingerprint != fingerprint:
                raise IdempotencyConflictError(f"idempotency key conflict: {operation}:{key}")
            row.result_json = _encode_result(result)
            row.state = "COMPLETED"
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
            return result


def _encode_result(value: Any) -> str:
    import json
    from dataclasses import asdict, is_dataclass
    if is_dataclass(value):
        value = asdict(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)


def _decode_result(value: str | None) -> Any:
    import json
    if value is None:
        return None
    return json.loads(value)


def build_postgres_session_factory(connection_string: str):
    engine = create_engine(connection_string, pool_pre_ping=True)
    IdempotencyBase.metadata.create_all(engine)
    return lambda: Session(engine)


__all__ = ["IdempotencyRecordModel", "IdempotencyReplay", "PostgreSQLIdempotencyStore", "build_postgres_session_factory"]
