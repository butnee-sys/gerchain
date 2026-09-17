"""Canonical schema/version authority persistence for CORE W3.

The domain transition contract lives in ``core.schema_authority``.  This module
is the persistence boundary: the canonical schema row is locked before the
predecessor/version check and the upgrade record plus successor state are
committed in one transaction.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import declarative_base, Session

from core.schema_authority import SchemaState, SchemaStatus, SchemaUpgrade, UpgradeStatus, apply_upgrade


SchemaAuthorityBase = declarative_base()


class CoreSchemaStateModel(SchemaAuthorityBase):
    __tablename__ = "core_schema_state"

    schema_id = Column(String(128), primary_key=True)
    current_version = Column(Integer, nullable=False)
    state_hash = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False)
    updated_at = Column(DateTime, nullable=False)


class CoreSchemaUpgradeModel(SchemaAuthorityBase):
    __tablename__ = "core_schema_upgrade"

    upgrade_id = Column(String(128), primary_key=True)
    schema_id = Column(String(128), nullable=False)
    from_version = Column(Integer, nullable=False)
    to_version = Column(Integer, nullable=False)
    migration_hash = Column(String(128), nullable=False)
    authority = Column(String(256), nullable=False)
    status = Column(String(32), nullable=False)
    created_at = Column(DateTime, nullable=False)
    applied_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "schema_id",
            "from_version",
            "to_version",
            "migration_hash",
            name="uq_core_schema_upgrade_transition",
        ),
    )


class SchemaUpgradeRejected(RuntimeError):
    """The requested upgrade cannot become authoritative."""


class SchemaUpgradeConflict(SchemaUpgradeRejected):
    """Another authoritative upgrade has advanced the predecessor version."""


class SchemaUpgradeAlreadyApplied(SchemaUpgradeRejected):
    """The requested upgrade identity is already applied."""


@dataclass(frozen=True)
class UpgradeResult:
    upgrade_id: str
    schema_id: str
    from_version: int
    to_version: int
    status: UpgradeStatus


def _state(model: CoreSchemaStateModel) -> SchemaState:
    return SchemaState(
        schema_id=model.schema_id,
        current_version=model.current_version,
        state_hash=model.state_hash,
        status=SchemaStatus(model.status),
    )


def create_schema_authority_tables(engine) -> None:
    """Create only the W3 authority tables; production migration ownership remains explicit."""
    SchemaAuthorityBase.metadata.create_all(engine)


def initialize_schema(session: Session, schema_id: str, version: int, state_hash: str) -> None:
    """Insert the sole canonical schema row. Re-initialization is rejected."""
    if session.get(CoreSchemaStateModel, schema_id) is not None:
        raise SchemaUpgradeConflict(f"schema already initialized: {schema_id}")
    session.add(
        CoreSchemaStateModel(
            schema_id=schema_id,
            current_version=version,
            state_hash=state_hash,
            status=SchemaStatus.ACTIVE.value,
            updated_at=datetime.utcnow(),
        )
    )
    session.flush()


def _existing_upgrade(session: Session, upgrade_id: str):
    return session.get(CoreSchemaUpgradeModel, upgrade_id)


def _result_from_existing(existing: CoreSchemaUpgradeModel, requested: SchemaUpgrade) -> UpgradeResult:
    if (
        existing.schema_id != requested.schema_id
        or existing.from_version != requested.from_version
        or existing.to_version != requested.to_version
        or existing.migration_hash != requested.migration_hash
        or existing.authority != requested.authority
    ):
        raise SchemaUpgradeConflict("migration identity conflict for existing migration_id")
    if existing.status == UpgradeStatus.APPLIED.value:
        return UpgradeResult(
            existing.upgrade_id,
            existing.schema_id,
            existing.from_version,
            existing.to_version,
            UpgradeStatus.APPLIED,
        )
    raise SchemaUpgradeConflict(f"upgrade identity exists with status={existing.status}")


def apply_upgrade_transaction(
    session: Session,
    upgrade: SchemaUpgrade,
    new_state_hash: str,
) -> UpgradeResult:
    """Atomically apply one schema upgrade under the canonical-row lock.

    PostgreSQL ``FOR UPDATE`` serializes all upgrades for the same schema.
    The upgrade identity is checked both before and after the lock so a
    concurrent retry can resolve to the already committed authoritative
    upgrade rather than being mistaken for a stale distinct upgrade.
    """
    existing = _existing_upgrade(session, upgrade.upgrade_id)
    if existing is not None:
        return _result_from_existing(existing, upgrade)

    current_model = (
        session.query(CoreSchemaStateModel)
        .filter(CoreSchemaStateModel.schema_id == upgrade.schema_id)
        .with_for_update()
        .one_or_none()
    )
    if current_model is None:
        raise SchemaUpgradeRejected(f"unknown schema: {upgrade.schema_id}")

    existing = _existing_upgrade(session, upgrade.upgrade_id)
    if existing is not None:
        return _result_from_existing(existing, upgrade)

    current = _state(current_model)
    try:
        successor = apply_upgrade(current, upgrade, new_state_hash)
    except Exception as exc:
        raise SchemaUpgradeConflict(str(exc)) from exc

    now = datetime.utcnow()
    session.add(
        CoreSchemaUpgradeModel(
            upgrade_id=upgrade.upgrade_id,
            schema_id=upgrade.schema_id,
            from_version=upgrade.from_version,
            to_version=upgrade.to_version,
            migration_hash=upgrade.migration_hash,
            authority=upgrade.authority,
            status=UpgradeStatus.APPLIED.value,
            created_at=now,
            applied_at=now,
        )
    )
    current_model.current_version = successor.current_version
    current_model.state_hash = successor.state_hash
    current_model.status = successor.status.value
    current_model.updated_at = now
    session.flush()
    return UpgradeResult(
        upgrade.upgrade_id,
        upgrade.schema_id,
        upgrade.from_version,
        upgrade.to_version,
        UpgradeStatus.APPLIED,
    )
