from pathlib import Path

import pytest

from postgres.migrations import apply_migrations


def test_repository_migration_versions_are_ordered():
    migration_dir = Path(__file__).resolve().parents[2] / "postgres" / "migrations"
    versions = [int(path.name.split("_", 1)[0]) for path in migration_dir.glob("*.sql")]
    assert versions == sorted(versions)
    assert len(versions) == len(set(versions))
    assert max(versions) >= 12
    assert 12 in versions


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
        6: "006_canonical_movement_integrity.sql",
    }
    for version, name in expected.items():
        candidates = [p for p in migration_dir.glob(f"{version:03d}_*.sql")]
        assert any(p.name == name for p in candidates)



def test_postgresql_migrations_use_valid_dollar_quoting():
    migration_dir = Path(__file__).resolve().parents[2] / "postgres" / "migrations"
    for path in migration_dir.glob("*.sql"):
        sql = path.read_text(encoding="utf-8")
        assert "DO $\n" not in sql, f"invalid dollar quote opener in {path.name}"
        assert "END $;" not in sql, f"invalid dollar quote closer in {path.name}"



def test_sql_splitter_preserves_dollar_quoted_blocks_and_semicolons():
    from postgres.migrations import _split_sql_statements

    sql = """
    CREATE TABLE example (id INTEGER);
    DO $$
    BEGIN
        PERFORM 1;
        PERFORM 2;
    END $$;
    CREATE INDEX example_id ON example (id);
    """
    statements = _split_sql_statements(sql)
    assert len(statements) == 3
    assert statements[1].startswith("DO $$")
    assert "PERFORM 1;" in statements[1]
    assert "PERFORM 2;" in statements[1]


def test_sql_splitter_preserves_single_quoted_semicolons():
    from postgres.migrations import _split_sql_statements

    statements = _split_sql_statements("INSERT INTO t VALUES ('a;b'); SELECT 1;")
    assert statements == ["INSERT INTO t VALUES ('a;b')", "SELECT 1"]
