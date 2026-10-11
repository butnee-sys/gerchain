"""Compatibility exports for the single canonical PostgreSQL migration runner.

The implementation lives only in :mod:`postgres.migrations`. This module
keeps the supported public API without importing removed historical helpers.
"""
from postgres.migrations import (
    _canonical_migration_files,
    _split_sql_statements,
    apply_migrations,
    checksum,
)

__all__ = [
    "apply_migrations",
    "checksum",
    "_canonical_migration_files",
    "_split_sql_statements",
]
