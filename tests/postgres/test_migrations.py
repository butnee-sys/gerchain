from pathlib import Path

import pytest

from postgres.migrations import _canonical_migration_files, apply_migrations, checksum


MIGRATION_DIR = Path(__file__).resolve().parents[2] / "postgres" / "migrations"

EXPECTED_CANONICAL_CHAIN = [
    "001_canonical_production.sql",
    "002_canonical_production.sql",
    "003_canonical_compatibility.sql",
    "004_canonical_value_truth.sql",
    "005_canonical_production.sql",
    "006_canonical_movement_integrity.sql",
    "007_canonical_production_reconciliation.sql",
    "008_ea35_idempotency_compat.sql",
    "009_canonical_movement_integrity_hardening.sql",
    "010_canonical_evidence_constraints.sql",
    "011_ea35_canonical_schema_finalization.sql",
    "012_canonical_production.sql",
    "013_ea35_canonical_schema_hardening.sql",
]


def test_repository_migration_versions_resolve_to_exact_canonical_chain():
    selected = _canonical_migration_files(MIGRATION_DIR)
    assert [path.name for path in selected] == EXPECTED_CANONICAL_CHAIN
    assert [int(path.name.split("_", 1)[0]) for path in selected] == list(range(1, 14))


def test_physical_historical_aliases_are_not_extra_active_migrations():
    physical = list(MIGRATION_DIR.glob("*.sql"))
    versions = [int(path.name.split("_", 1)[0]) for path in physical]
    duplicates = {version for version in versions if versions.count(version) > 1}
    assert duplicates == {1, 2, 3, 4, 5}
    assert len(_canonical_migration_files(MIGRATION_DIR)) == 13


def test_selected_migration_checksum_is_sha256_of_exact_utf8_source():
    selected = _canonical_migration_files(MIGRATION_DIR)
    for path in selected:
        source = path.read_text(encoding="utf-8")
        assert checksum(source)
        assert len(checksum(source)) == 64
        assert all(character in "0123456789abcdef" for character in checksum(source))


def test_unresolved_duplicate_migration_version_fails_closed(tmp_path: Path):
    (tmp_path / "001_first.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "001_duplicate.sql").write_text("SELECT 2;", encoding="utf-8")

    class DummyConnection:
        def in_transaction(self):
            return False

    with pytest.raises(RuntimeError, match="ambiguous migration version 1"):
        apply_migrations(DummyConnection(), tmp_path)


def test_known_canonical_alias_versions_have_deterministic_preferred_files():
    # This is the legacy schema directory, not the active canonical migration source.
    legacy_dir = Path(__file__).resolve().parents[2] / "postgres" / "schema"
    expected = {
        2: "002_canonical_production.sql",
        5: "005_canonical_production.sql",
        6: "006_canonical_movement_integrity.sql",
    }
    for version, name in expected.items():
        candidates = [path for path in legacy_dir.glob(f"{version:03d}_*.sql")]
        assert any(path.name == name for path in candidates)


def test_postgresql_migrations_use_valid_dollar_quoting():
    for path in MIGRATION_DIR.glob("*.sql"):
        source = path.read_text(encoding="utf-8")
        assert "DO $\n" not in source, f"invalid dollar quote opener in {path.name}"
        assert "END $;" not in source, f"invalid dollar quote closer in {path.name}"


def test_sql_splitter_preserves_dollar_quoted_blocks_and_semicolons():
    from postgres.migrations import _split_sql_statements

    source = """
    CREATE TABLE example (id INTEGER);
    DO $$
    BEGIN
        PERFORM 1;
        PERFORM 2;
    END $$;
    CREATE INDEX example_id ON example (id);
    """
    statements = _split_sql_statements(source)
    assert len(statements) == 3
    assert statements[1].startswith("DO $$")
    assert "PERFORM 1;" in statements[1]
    assert "PERFORM 2;" in statements[1]


def test_sql_splitter_preserves_single_quoted_semicolons():
    from postgres.migrations import _split_sql_statements

    statements = _split_sql_statements("INSERT INTO t VALUES ('a;b'); SELECT 1;")
    assert statements == ["INSERT INTO t VALUES ('a;b')", "SELECT 1"]


def test_compatibility_runner_reexports_the_single_canonical_runner():
    from postgres import migration_runner, migrations

    assert migration_runner.apply_migrations is migrations.apply_migrations
    assert migration_runner.checksum is migrations.checksum
