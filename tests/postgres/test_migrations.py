from pathlib import Path

import pytest

from postgres.migrations import apply_migrations


def test_repository_migration_versions_are_unique() -> None:
    migration_dir = Path(__file__).resolve().parents[2] / "postgres" / "migrations"
    versions = [int(path.name.split("_", 1)[0]) for path in migration_dir.glob("*.sql")]
    assert versions == sorted(set(versions))


def test_duplicate_migration_version_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "001_first.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "001_duplicate.sql").write_text("SELECT 2;", encoding="utf-8")

    class DummyConnection:
        def in_transaction(self):
            return False

    with pytest.raises(RuntimeError, match="Duplicate migration version 1"):
        apply_migrations(DummyConnection(), tmp_path)
