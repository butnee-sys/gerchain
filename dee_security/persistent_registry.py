"""Persistent DEE owner-key registry backed by SQLAlchemy.

The registry stores public key metadata and rotation replay state only.
Private keys never enter this database. PostgreSQL row locks are used for
rotation serialization; database uniqueness constraints provide a second
line of defense against duplicate active keys and rotation identifiers.
"""
from __future__ import annotations

import base64
import json
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy import DateTime, Index, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from .key_management import OwnerKeyRecord
from .root_of_trust import SecurityError
from .rotation import KeyRotationRequest, key_id_from_public_key


class Base(DeclarativeBase):
    pass


class OwnerKeyRow(Base):
    __tablename__ = "dee_owner_keys"

    key_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(255), index=True)
    public_key_b64: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rotated_from: Mapped[str | None] = mapped_column(String(128), nullable=True)


Index(
    "uq_dee_owner_one_active_key",
    OwnerKeyRow.owner_id,
    unique=True,
    postgresql_where=OwnerKeyRow.status == "active",
    sqlite_where=OwnerKeyRow.status == "active",
)


class RotationReplayRow(Base):
    __tablename__ = "dee_key_rotation_replays"

    rotation_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PersistentKeyRegistry:
    """Transaction-safe owner-key registry.

    A PostgreSQL URL should be used in production. SQLite remains useful for
    local tests. Rotation is serialized on the current active-key row, while
    the partial unique index guarantees one active key per owner.
    """

    def __init__(self, database_url: str, initial: OwnerKeyRecord | None = None) -> None:
        self.engine = create_engine(database_url, future=True)
        Base.metadata.create_all(self.engine)
        if initial is not None:
            self._ensure_initial(initial)

    def _ensure_initial(self, record: OwnerKeyRecord) -> None:
        with Session(self.engine) as session, session.begin():
            existing = session.get(OwnerKeyRow, record.key_id)
            if existing is None:
                active = session.scalar(
                    select(OwnerKeyRow).where(
                        OwnerKeyRow.owner_id == record.owner_id,
                        OwnerKeyRow.status == "active",
                    ).limit(1)
                )
                if active is not None and active.key_id != record.key_id:
                    raise SecurityError("owner already has an active key")
                session.add(OwnerKeyRow(
                    key_id=record.key_id,
                    owner_id=record.owner_id,
                    public_key_b64=record.public_key_b64,
                    status=record.status,
                    created_at=datetime.now(timezone.utc),
                    rotated_from=record.rotated_from,
                ))

    def active(self, owner_id: str) -> OwnerKeyRecord:
        with Session(self.engine) as session:
            row = session.scalar(
                select(OwnerKeyRow).where(
                    OwnerKeyRow.owner_id == owner_id,
                    OwnerKeyRow.status == "active",
                ).limit(1)
            )
            if row is None:
                raise SecurityError("DEE owner has no active key")
            return self._record(row)

    def _record(self, row: OwnerKeyRow) -> OwnerKeyRecord:
        return OwnerKeyRecord(
            owner_id=row.owner_id,
            key_id=row.key_id,
            public_key_b64=row.public_key_b64,
            status=row.status,
            created_at=row.created_at.isoformat(),
            rotated_from=row.rotated_from,
        )

    def apply_rotation(self, request: KeyRotationRequest, current_public_key: Ed25519PublicKey) -> OwnerKeyRecord:
        """Authorize and atomically apply one owner-key rotation."""
        with Session(self.engine) as session:
            try:
                with session.begin():
                    replay = session.get(RotationReplayRow, request.rotation_id)
                    if replay is not None:
                        raise SecurityError("rotation replay detected")

                    current = session.scalar(
                        select(OwnerKeyRow)
                        .where(
                            OwnerKeyRow.owner_id == request.owner_id,
                            OwnerKeyRow.status == "active",
                        )
                        .with_for_update()
                        .limit(1)
                    )
                    if current is None:
                        raise SecurityError("DEE owner has no active key")
                    if current.key_id != request.current_key_id:
                        raise SecurityError("rotation must use the active owner key")
                    if key_id_from_public_key(current_public_key) != current.key_id:
                        raise SecurityError("current public key does not match active key")
                    try:
                        current_public_key.verify(
                            base64.b64decode(request.signature.encode("ascii"), validate=True),
                            request_signing_payload(request),
                        )
                        raw = base64.b64decode(request.new_public_key_b64.encode("ascii"), validate=True)
                        derived = key_id_from_public_key(Ed25519PublicKey.from_public_bytes(raw))
                    except Exception as exc:
                        raise SecurityError("invalid key rotation signature or public key") from exc
                    if derived != request.new_key_id:
                        raise SecurityError("new key fingerprint mismatch")
                    if session.get(OwnerKeyRow, request.new_key_id) is not None:
                        raise SecurityError("new owner key already exists")

                    current.status = "revoked"
                    session.add(OwnerKeyRow(
                        key_id=request.new_key_id,
                        owner_id=request.owner_id,
                        public_key_b64=request.new_public_key_b64,
                        status="active",
                        created_at=datetime.now(timezone.utc),
                        rotated_from=current.key_id,
                    ))
                    session.add(RotationReplayRow(
                        rotation_id=request.rotation_id,
                        owner_id=request.owner_id,
                        created_at=datetime.now(timezone.utc),
                    ))
                return self.active(request.owner_id)
            except SecurityError:
                session.rollback()
                raise


def request_signing_payload(request: KeyRotationRequest) -> bytes:
    return json.dumps(
        request.signing_payload(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
