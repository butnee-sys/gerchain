"""Canonical PostgreSQL schema/version authority contract.

This module contains the domain state machine only. Persistence, migration
execution, and SQL locking are deliberately kept outside the domain object so
that the authority relation can be independently tested and reproduced.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SchemaAuthorityError(ValueError):
    pass


class SchemaStatus(str, Enum):
    ACTIVE = "ACTIVE"
    UPGRADING = "UPGRADING"
    FAILED = "FAILED"


class UpgradeStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class SchemaState:
    schema_id: str
    current_version: int
    state_hash: str
    status: SchemaStatus = SchemaStatus.ACTIVE


@dataclass(frozen=True)
class SchemaUpgrade:
    upgrade_id: str
    schema_id: str
    from_version: int
    to_version: int
    migration_hash: str
    authority: str
    status: UpgradeStatus = UpgradeStatus.REQUESTED

    def validate(self, current: SchemaState) -> None:
        if self.schema_id != current.schema_id:
            raise SchemaAuthorityError("schema identity mismatch")
        if self.from_version != current.current_version:
            raise SchemaAuthorityError("stale schema predecessor")
        if self.to_version <= self.from_version:
            raise SchemaAuthorityError("schema version must increase")
        if not self.upgrade_id or not self.migration_hash or not self.authority:
            raise SchemaAuthorityError("upgrade identity, migration hash and authority are required")


def apply_upgrade(current: SchemaState, upgrade: SchemaUpgrade, new_state_hash: str) -> SchemaState:
    """Return the only valid successor state for an authorized upgrade.

    The database adapter must serialize the predecessor check and persistence
    of this successor in one transaction. This pure function does not claim
    database atomicity by itself.
    """
    upgrade.validate(current)
    if current.status != SchemaStatus.ACTIVE:
        raise SchemaAuthorityError("schema is not available for upgrade")
    if not new_state_hash:
        raise SchemaAuthorityError("new schema state hash is required")
    return SchemaState(
        schema_id=current.schema_id,
        current_version=upgrade.to_version,
        state_hash=new_state_hash,
        status=SchemaStatus.ACTIVE,
    )


__all__ = [
    "SchemaAuthorityError",
    "SchemaState",
    "SchemaStatus",
    "SchemaUpgrade",
    "UpgradeStatus",
    "apply_upgrade",
]
