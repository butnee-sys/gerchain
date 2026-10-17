"""Canonical schema/version authority persistence for CORE W3."""
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
    __table_args__ = (UniqueConstraint("schema_id", "from_version", "to_version", "migration_hash", name="uq_core_schema_upgrade_transition"),)


class CoreMigrationIdentityModel(SchemaAuthorityBase):
    """Durable identity reservation, separate from authoritative schema state.

    Reservation survives a failed DDL transaction, so the same migration ID
    cannot later be reused with a different payload/hash.
    """
    __tablename__ = "core_migration_identity"
    migration_id = Column(String(128), primary_key=True)
    schema_id = Column(String(128), nullable=False)
    from_version = Column(Integer, nullable=False)
    to_version = Column(Integer, nullable=False)
    migration_hash = Column(String(128), nullable=False)
    authority = Column(String(256), nullable=False)
    status = Column(String(32), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class SchemaUpgradeRejected(RuntimeError):
    """The requested upgrade cannot become authoritative."""
class SchemaUpgradeConflict(SchemaUpgradeRejected):
    """Another authoritative upgrade or identity conflicts with the request."""
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
    return SchemaState(model.schema_id, model.current_version, model.state_hash, SchemaStatus(model.status))


def create_schema_authority_tables(engine) -> None:
    SchemaAuthorityBase.metadata.create_all(engine)


def initialize_schema(session: Session, schema_id: str, version: int, state_hash: str) -> None:
    if session.get(CoreSchemaStateModel, schema_id) is not None:
        raise SchemaUpgradeConflict(f"schema already initialized: {schema_id}")
    session.add(CoreSchemaStateModel(schema_id=schema_id, current_version=version, state_hash=state_hash, status=SchemaStatus.ACTIVE.value, updated_at=datetime.utcnow()))
    session.flush()


def _existing_upgrade(session: Session, upgrade_id: str):
    return session.get(CoreSchemaUpgradeModel, upgrade_id)


def _result_from_existing(existing: CoreSchemaUpgradeModel, requested: SchemaUpgrade) -> UpgradeResult:
    if (existing.schema_id, existing.from_version, existing.to_version, existing.migration_hash, existing.authority) != (requested.schema_id, requested.from_version, requested.to_version, requested.migration_hash, requested.authority):
        raise SchemaUpgradeConflict("migration identity conflict for existing migration_id")
    if existing.status == UpgradeStatus.APPLIED.value:
        return UpgradeResult(existing.upgrade_id, existing.schema_id, existing.from_version, existing.to_version, UpgradeStatus.APPLIED)
    raise SchemaUpgradeConflict(f"upgrade identity exists with status={existing.status}")


def reserve_migration_identity(session: Session, upgrade: SchemaUpgrade) -> None:
    """Durably reserve an immutable migration identity before DDL execution."""
    existing = session.get(CoreMigrationIdentityModel, upgrade.upgrade_id)
    if existing is not None:
        if (existing.schema_id, existing.from_version, existing.to_version, existing.migration_hash, existing.authority) != (upgrade.schema_id, upgrade.from_version, upgrade.to_version, upgrade.migration_hash, upgrade.authority):
            raise SchemaUpgradeConflict("migration identity conflict for existing migration_id")
        return
    now = datetime.utcnow()
    session.add(CoreMigrationIdentityModel(
        migration_id=upgrade.upgrade_id, schema_id=upgrade.schema_id,
        from_version=upgrade.from_version, to_version=upgrade.to_version,
        migration_hash=upgrade.migration_hash, authority=upgrade.authority,
        status="RESERVED", created_at=now, updated_at=now,
    ))
    session.flush()


def mark_migration_identity(session: Session, upgrade_id: str, status: str) -> None:
    identity = session.get(CoreMigrationIdentityModel, upgrade_id)
    if identity is None:
        raise SchemaUpgradeConflict(f"unknown migration identity: {upgrade_id}")
    identity.status = status
    identity.updated_at = datetime.utcnow()
    session.flush()


def apply_upgrade_transaction(session: Session, upgrade: SchemaUpgrade, new_state_hash: str) -> UpgradeResult:
    existing = _existing_upgrade(session, upgrade.upgrade_id)
    if existing is not None:
        return _result_from_existing(existing, upgrade)
    current_model = session.query(CoreSchemaStateModel).filter(CoreSchemaStateModel.schema_id == upgrade.schema_id).with_for_update().one_or_none()
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
    session.add(CoreSchemaUpgradeModel(upgrade_id=upgrade.upgrade_id, schema_id=upgrade.schema_id, from_version=upgrade.from_version, to_version=upgrade.to_version, migration_hash=upgrade.migration_hash, authority=upgrade.authority, status=UpgradeStatus.APPLIED.value, created_at=now, applied_at=now))
    current_model.current_version = successor.current_version
    current_model.state_hash = successor.state_hash
    current_model.status = successor.status.value
    current_model.updated_at = now
    session.flush()
    return UpgradeResult(upgrade.upgrade_id, upgrade.schema_id, upgrade.from_version, upgrade.to_version, UpgradeStatus.APPLIED)
