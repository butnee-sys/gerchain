from pathlib import Path

import pytest

from postgres.migrations import CANONICAL_MIGRATION_NAMES, _canonical_migration_files
from scripts.postgres_migration_runner import CANONICAL_MIGRATION_DIR
from scripts.apply_postgres_migration import apply_migration


def test_canonical_manifest_matches_physical_migration_files():
    """Every canonical version maps to exactly its frozen physical filename."""
    files = _canonical_migration_files(CANONICAL_MIGRATION_DIR)
    actual = {
        int(path.name.split("_", 1)[0]): path.name
        for path in files
    }
    assert actual == CANONICAL_MIGRATION_NAMES
    assert sorted(actual) == list(range(1, len(CANONICAL_MIGRATION_NAMES) + 1))
    assert len({path.name for path in files}) == len(files)


def test_legacy_schema_runner_rejects_standalone_sql_without_connecting():
    """The compatibility entrypoint must not execute postgres/schema/*.sql."""
    legacy_path = Path(__file__).resolve().parents[1] / "schema" / "001_concurrency.sql"
    with pytest.raises(ValueError, match="standalone postgres/schema migration execution is disabled"):
        apply_migration("postgresql://invalid/unused", legacy_path)


def test_compatibility_runner_selects_canonical_version_one_by_default():
    from scripts.apply_postgres_migration import MIGRATION_PATH

    assert MIGRATION_PATH.parent.resolve() == CANONICAL_MIGRATION_DIR.resolve()
    assert MIGRATION_PATH.name == CANONICAL_MIGRATION_NAMES[1]
