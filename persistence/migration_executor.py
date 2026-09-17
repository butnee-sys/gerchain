"""CORE-owned transactional PostgreSQL migration executor for W3.1-B."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.migration_identity import MigrationIdentity, MigrationIdentityError
from core.schema_authority import SchemaUpgrade
from persistence.schema_authority import UpgradeResult, apply_upgrade_transaction
from persistence.schema_reconciler import DESCRIPTOR_VERSION, physical_schema_fingerprint, reconcile


class MigrationExecutionError(RuntimeError):
    """Migration cannot be executed or cannot be proven committed."""


class MigrationBypassError(MigrationExecutionError):
    """DDL is outside the explicitly supported transactional migration class."""


class MigrationSchemaMismatch(MigrationExecutionError):
    """DDL completed but actual PostgreSQL schema did not match the declaration."""


@dataclass(frozen=True)
class MigrationDefinition:
    identity: MigrationIdentity
    statements: tuple[str, ...]
    expected_schema_hash: str
    descriptor_version: str = DESCRIPTOR_VERSION
    namespaces: tuple[str, ...] = ("core",)
    authority: str = "CORE-W3.1B"

    def validate(self) -> None:
        self.identity.validate()
        if self.identity.migration_hash != migration_hash(self.statements):
            raise MigrationIdentityError("migration_hash does not match canonical DDL payload")
        if not self.expected_schema_hash:
            raise MigrationExecutionError("expected_schema_hash is required")
        if self.descriptor_version != DESCRIPTOR_VERSION:
            raise MigrationBypassError("unsupported schema descriptor version")
        if not self.namespaces:
            raise MigrationBypassError("at least one declared namespace is required")
        if not self.statements:
            raise MigrationBypassError("empty migration payload")
        for statement in self.statements:
            _validate_statement(statement)


def canonical_ddl(statements: tuple[str, ...]) -> bytes:
    return "\n".join(_normalize_sql(s) for s in statements).encode("utf-8")


def migration_hash(statements: tuple[str, ...]) -> str:
    return hashlib.sha256(canonical_ddl(statements)).hexdigest()


_ALLOWED_PREFIXES = (
    "CREATE TABLE ",
    "CREATE INDEX ",
    "CREATE UNIQUE INDEX ",
    "ALTER TABLE ",
)
_FORBIDDEN_TOKENS = (
    "BEGIN",
    "COMMIT",
    "ROLLBACK",
    "SAVEPOINT",
    "RELEASE SAVEPOINT",
    "CREATE DATABASE",
    "DROP DATABASE",
    "CREATE EXTENSION",
    "ALTER SYSTEM",
    "COPY ",
    "CONCURRENTLY",
)
_FORBIDDEN_CREATE_TABLE_TOKENS = (
    " CREATE TABLE AS ",
    "CREATE TABLE IF NOT EXISTS ",
    " PARTITION ",
    " INHERITS ",
    " LIKE ",
)
_FORBIDDEN_ALTER_TOKENS = (
    " DROP ",
    " RENAME ",
    " SET SCHEMA ",
    " OWNER TO ",
    " ENABLE ",
    " DISABLE ",
    " NO INHERIT ",
    " CLUSTER ON ",
)


def _normalize_sql(statement: str) -> str:
    value = statement.strip()
    if value.endswith(";"):
        value = value[:-1]
    return re.sub(r"\s+", " ", value).strip()


def _validate_statement(statement: str) -> None:
    normalized = _normalize_sql(statement)
    if not normalized:
        raise MigrationBypassError("empty DDL statement")
    upper = normalized.upper()
    if any(token in upper for token in _FORBIDDEN_TOKENS):
        raise MigrationBypassError("transaction/control or unsupported DDL token rejected")
    if not upper.startswith(_ALLOWED_PREFIXES):
        raise MigrationBypassError("DDL statement is outside W3.1-B supported migration class")
    if ";" in normalized:
        raise MigrationBypassError("multiple SQL statements in one migration item are rejected")
    if upper.startswith("CREATE TABLE "):
        if any(token in f" {upper} " for token in _FORBIDDEN_CREATE_TABLE_TOKENS):
            raise MigrationBypassError("unsupported CREATE TABLE form")
    elif upper.startswith("CREATE INDEX ") or upper.startswith("CREATE UNIQUE INDEX "):
        if " WHERE " in f" {upper} " or " USING " in f" {upper} " and " USING BTREE " not in f" {upper} ":
            raise MigrationBypassError("unsupported index form")
    elif upper.startswith("ALTER TABLE "):
        if any(token in f" {upper} " for token in _FORBIDDEN_ALTER_TOKENS):
            raise MigrationBypassError("unsupported ALTER TABLE operation")
        allowed = (
            " ADD COLUMN ",
            " ALTER COLUMN ",
            " ADD CONSTRAINT ",
        )
        if not any(token in f" {upper} " for token in allowed):
            raise MigrationBypassError("ALTER TABLE operation is outside W3.1-B supported class")
        if "ALTER COLUMN" in upper:
            if not any(op in f" {upper} " for op in (" TYPE ", " SET NOT NULL", " DROP NOT NULL", " SET DEFAULT ", " DROP DEFAULT")):
                raise MigrationBypassError("unsupported ALTER COLUMN operation")
        if "ADD CONSTRAINT" in upper and not any(kind in upper for kind in (" PRIMARY KEY", " UNIQUE", " CHECK ", " FOREIGN KEY")):
            raise MigrationBypassError("unsupported constraint type")


def _authority_upgrade(definition: MigrationDefinition) -> SchemaUpgrade:
    return SchemaUpgrade(
        upgrade_id=definition.identity.migration_id,
        schema_id=definition.identity.schema_id,
        from_version=definition.identity.from_version,
        to_version=definition.identity.to_version,
        migration_hash=definition.identity.migration_hash,
        authority=definition.authority,
    )


def _verify_physical_state(session: Session, definition: MigrationDefinition) -> None:
    descriptor, actual_hash = reconcile(
        session.connection(),
        definition.identity.schema_id,
        definition.expected_schema_hash,
        definition.namespaces,
    )
    if descriptor.descriptor_version != definition.descriptor_version:
        raise MigrationSchemaMismatch("descriptor version mismatch")
    if actual_hash != definition.expected_schema_hash:
        raise MigrationSchemaMismatch(
            f"actual schema fingerprint mismatch: expected={definition.expected_schema_hash} actual={actual_hash}"
        )


def _verify_recorded_predecessor(session: Session, state, definition: MigrationDefinition) -> None:
    """Require actual physical state to equal the W3-recorded predecessor."""
    descriptor, actual_hash = reconcile(
        session.connection(),
        definition.identity.schema_id,
        definition.expected_schema_hash,
        definition.namespaces,
    )
    if descriptor.descriptor_version != definition.descriptor_version:
        raise MigrationSchemaMismatch("descriptor version mismatch in recorded predecessor")
    if actual_hash != state.state_hash:
        raise MigrationSchemaMismatch(
            f"recorded predecessor mismatch: recorded={state.state_hash} actual={actual_hash}"
        )


def execute_migration(session: Session, definition: MigrationDefinition) -> UpgradeResult:
    """Execute one W3.1-B migration inside the caller's transaction."""
    definition.validate()

    from persistence.schema_authority import CoreSchemaStateModel, CoreSchemaUpgradeModel

    existing = session.get(CoreSchemaUpgradeModel, definition.identity.migration_id)
    if existing is not None:
        _verify_physical_state(session, definition)
        return apply_upgrade_transaction(session, _authority_upgrade(definition), definition.expected_schema_hash)

    connection = session.connection()
    state = (
        session.query(CoreSchemaStateModel)
        .filter(CoreSchemaStateModel.schema_id == definition.identity.schema_id)
        .with_for_update()
        .one_or_none()
    )
    if state is None:
        raise MigrationExecutionError(f"unknown schema: {definition.identity.schema_id}")

    existing = session.get(CoreSchemaUpgradeModel, definition.identity.migration_id)
    if existing is not None:
        _verify_physical_state(session, definition)
        return apply_upgrade_transaction(session, _authority_upgrade(definition), definition.expected_schema_hash)

    if state.current_version != definition.identity.from_version:
        raise MigrationExecutionError("stale schema predecessor")
    if state.status != "ACTIVE":
        raise MigrationExecutionError("schema is not available for migration")

    # Recovery is predecessor-based, never target-adoption based.
    _verify_recorded_predecessor(session, state, definition)

    for statement in definition.statements:
        connection.execute(text(_normalize_sql(statement)))

    _verify_physical_state(session, definition)
    descriptor, _ = reconcile(
        connection,
        definition.identity.schema_id,
        definition.expected_schema_hash,
        definition.namespaces,
    )
    return apply_upgrade_transaction(
        session,
        _authority_upgrade(definition),
        physical_schema_fingerprint(descriptor),
    )


__all__ = [
    "MigrationDefinition",
    "MigrationExecutionError",
    "MigrationBypassError",
    "MigrationSchemaMismatch",
    "canonical_ddl",
    "migration_hash",
    "execute_migration",
]
