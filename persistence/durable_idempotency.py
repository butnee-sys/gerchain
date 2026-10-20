from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy import DateTime, Integer, String, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from core.idempotency import IdempotencyConflictError, IdempotencyEngine


class IdempotencyBase(DeclarativeBase):
    pass


class DurableIdempotencyRecord(IdempotencyBase):
    """Authoritative durable request record; never a value-movement store."""

    __tablename__ = "gerchain_idempotency_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="COMPLETED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def get_existing_in_transaction(
    session: Session,
    *,
    key: str,
    payload: Mapping[str, Any],
) -> str | None:
    """Return a completed result for replay, or None when no durable record exists.

    Unlike begin_in_transaction(), this read-only gate never creates PROCESSING
    state. It is used by lifecycle wrappers that must validate the current
    aggregate state while still allowing a completed replay after a terminal
    transition.
    """
    if not key:
        raise ValueError("idempotency key is required")
    fingerprint = IdempotencyEngine.fingerprint(payload)
    existing = session.execute(
        select(DurableIdempotencyRecord)
        .where(DurableIdempotencyRecord.key == key)
        .with_for_update()
    ).scalar_one_or_none()
    if existing is None:
        return None
    if existing.fingerprint != fingerprint:
        raise IdempotencyConflictError(
            f"idempotency key reused with different request: {key}"
        )
    if existing.state == "COMPLETED":
        return existing.result_json
    if existing.state == "PROCESSING":
        raise RuntimeError(f"idempotency request already processing: {key}")
    raise RuntimeError(f"unknown idempotency state: {existing.state}")


def begin_in_transaction(
    session: Session,
    *,
    key: str,
    payload: Mapping[str, Any],
) -> str | None:
    if not key:
        raise ValueError("idempotency key is required")

    fingerprint = IdempotencyEngine.fingerprint(payload)
    existing = session.execute(
        select(DurableIdempotencyRecord)
        .where(DurableIdempotencyRecord.key == key)
        .with_for_update()
    ).scalar_one_or_none()

    if existing is None:
        session.add(
            DurableIdempotencyRecord(
                key=key,
                fingerprint=fingerprint,
                result_json=None,
                state="PROCESSING",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        return None

    if existing.fingerprint != fingerprint:
        raise IdempotencyConflictError(
            f"idempotency key reused with different request: {key}"
        )

    if existing.state == "COMPLETED":
        return existing.result_json

    if existing.state == "PROCESSING":
        raise RuntimeError(f"idempotency request already processing: {key}")

    raise RuntimeError(f"unknown idempotency state: {existing.state}")


def complete_in_transaction(
    session: Session,
    *,
    key: str,
    payload: Mapping[str, Any],
    result_json: str,
) -> str:
    fingerprint = IdempotencyEngine.fingerprint(payload)
    existing = session.execute(
        select(DurableIdempotencyRecord)
        .where(DurableIdempotencyRecord.key == key)
        .with_for_update()
    ).scalar_one()

    if existing.fingerprint != fingerprint:
        raise IdempotencyConflictError(
            f"idempotency key reused with different request: {key}"
        )

    if existing.state == "COMPLETED":
        if existing.result_json != result_json:
            raise IdempotencyConflictError(
                f"completed idempotency result conflict: {key}"
            )
        return existing.result_json or ""

    if existing.state != "PROCESSING":
        raise RuntimeError(f"cannot complete idempotency state: {existing.state}")

    existing.result_json = result_json
    existing.state = "COMPLETED"
    existing.updated_at = datetime.now(timezone.utc)
    return result_json


__all__ = [
    "DurableIdempotencyRecord",
    "begin_in_transaction",
    "get_existing_in_transaction",
    "complete_in_transaction",
]
