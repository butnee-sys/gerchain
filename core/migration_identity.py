"""Immutable identity contract for CORE production schema migrations."""
from __future__ import annotations

from dataclasses import dataclass


class MigrationIdentityError(ValueError):
    """Migration identity is malformed or conflicts with an existing identity."""


@dataclass(frozen=True)
class MigrationIdentity:
    migration_id: str
    schema_id: str
    from_version: int
    to_version: int
    migration_hash: str

    def validate(self) -> None:
        if not self.migration_id:
            raise MigrationIdentityError("migration_id is required")
        if not self.schema_id:
            raise MigrationIdentityError("schema_id is required")
        if not self.migration_hash:
            raise MigrationIdentityError("migration_hash is required")
        if self.from_version < 0 or self.to_version < 0:
            raise MigrationIdentityError("schema versions must be non-negative")
        if self.to_version <= self.from_version:
            raise MigrationIdentityError("migration must advance schema version")

    def same_identity(self, other: "MigrationIdentity") -> bool:
        return self == other

    def same_migration_id(self, other: "MigrationIdentity") -> bool:
        return self.migration_id == other.migration_id

    def conflicts_with(self, other: "MigrationIdentity") -> bool:
        """Return true when one MigrationID is reused for a different identity."""
        return self.same_migration_id(other) and not self.same_identity(other)

    def predecessor_matches(self, schema_id: str, current_version: int) -> bool:
        return self.schema_id == schema_id and self.from_version == current_version


__all__ = ["MigrationIdentity", "MigrationIdentityError"]
