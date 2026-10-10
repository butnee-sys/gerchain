"""Compatibility imports for the single canonical PostgreSQL migration runner.
New code and production construction must import :mod:`postgres.migrations`.
This module intentionally contains no independent migration implementation.
"""
from postgres.migrations import (
    FROZEN_CHECKSUMS,
    LEGACY_CHECKSUMS,
    MIGRATION_LOCK_KEY,
    _canonical_migration_files,
    _connection_in_transaction,
    _execute,
    _split_sql_statements,
    apply_migrations,
    checksum,
)

__all__ = [
    "FROZEN_CHECKSUMS",
    "LEGACY_CHECKSUMS",
    "MIGRATION_LOCK_KEY",
    "apply_migrations",
    "checksum",
]
