from pathlib import Path

import pytest

from postgres.migrations import apply_migrations


def test_repository_migration_versions_are_ordered():
    migration_dir = Path(__file__).resolve().parents[2] / "postgres" / "schema"
    versions = [int(path.name.split("_", 1)[0]) for path in migration_dir.glob("*.sql")]
    assert versions == sorted(versions)


def test_unresolved_duplicate_migration_version_fails_closed(tmp_path: Path):
    (tmp_path / "001_first.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "001_duplicate.sql").write_text("SELECT 2;", encoding="utf-8")

    class DummyConnection:
        def in_transaction(self):
            return False

    with pytest.raises(RuntimeError, match="Unresolved duplicate migration version 1"):
        apply_migrations(DummyConnection(), tmp_path)


def test_known_canonical_alias_versions_have_deterministic_preferred_files():
    migration_dir = Path(__file__).resolve().parents[2] / "postgres" / "schema"
    expected = {
        2: "002_canonical_production.sql",
        5: "005_canonical_production.sql",
        6: "006_canonical_escrow_lifecycle_hardening.sql",
    }
    for version, name in expected.items():
        candidates = [p for p in migration_dir.glob(f"{version:03d}_*.sql")]
        assert any(p.name == name for p in candidates)
