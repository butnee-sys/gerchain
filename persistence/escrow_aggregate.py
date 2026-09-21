from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, Numeric, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class EscrowBase(DeclarativeBase):
    pass


class EscrowState(StrEnum):
    CREATED = "CREATED"
    FUNDED = "FUNDED"
    LOCKED = "LOCKED"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


_ALLOWED_TRANSITIONS = {
    EscrowState.CREATED: {EscrowState.FUNDED, EscrowState.CANCELLED},
    EscrowState.FUNDED: {EscrowState.LOCKED, EscrowState.CANCELLED},
    EscrowState.LOCKED: {EscrowState.RELEASED, EscrowState.REFUNDED},
    EscrowState.RELEASED: set(),
    EscrowState.REFUNDED: set(),
    EscrowState.CANCELLED: set(),
}


class CanonicalEscrow(EscrowBase):
    """Durable representation of the existing canonical escrow aggregate."""

    __tablename__ = "escrows"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    sender_address: Mapped[str] = mapped_column(String, nullable=False)
    receiver_address: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(38, 8), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default=EscrowState.CREATED.value)
    condition_desc: Mapped[str | None] = mapped_column(String, nullable=True)
    refund_destination: Mapped[str | None] = mapped_column(String, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(16), nullable=True)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def transition_escrow(
    session: Session,
    escrow_id: str,
    expected_state: EscrowState,
    new_state: EscrowState,
) -> CanonicalEscrow:
    escrow = session.execute(
        select(CanonicalEscrow)
        .where(CanonicalEscrow.id == escrow_id)
        .with_for_update()
    ).scalar_one()

    actual = EscrowState(escrow.state)
    if actual != expected_state:
        raise ValueError(
            f"escrow {escrow_id} expected {expected_state.value}, got {actual.value}"
        )
    if new_state not in _ALLOWED_TRANSITIONS[actual]:
        raise ValueError(
            f"invalid escrow transition: {actual.value} -> {new_state.value}"
        )

    escrow.state = new_state.value
    escrow.version += 1
    escrow.updated_at = datetime.now(timezone.utc)
    return escrow


__all__ = ["CanonicalEscrow", "EscrowState", "transition_escrow"]
