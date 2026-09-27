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


def test_canonical_migration_005_uses_valid_postgresql_dollar_quoting() -> None:
    migration = (
        Path(__file__).resolve().parents[2]
        / "postgres"
        / "migrations"
        / "005_canonical_production_persistence.sql"
    ).read_text(encoding="utf-8")
    assert "DO $$" in migration
    assert "END $$;" in migration
    assert "DO $\n" not in migration
    assert "END $;" not in migration
