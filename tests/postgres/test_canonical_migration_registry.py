from __future__ import annotations

from pathlib import Path

import pytest

from postgres.migrations import (
    CANONICAL_MIGRATION_NAMES,
    _canonical_migration_files,
    _split_sql_statements,
)


def _write_chain(directory: Path, *, through: int = 17) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for version, name in CANONICAL_MIGRATION_NAMES.items():
        if version > through:
            break
        (directory / name).write_text(
            f"-- migration {version}\nSELECT {version};\n",
            encoding="utf-8",
        )


def test_canonical_migration_registry_selects_exact_ordered_chain(tmp_path):
    _write_chain(tmp_path)
    selected = _canonical_migration_files(tmp_path)
    assert [path.name for path in selected] == [
        CANONICAL_MIGRATION_NAMES[version] for version in range(1, 18)
    ]


def test_canonical_migration_registry_rejects_missing_version(tmp_path):
    _write_chain(tmp_path)
    (tmp_path / CANONICAL_MIGRATION_NAMES[8]).unlink()
    with pytest.raises(RuntimeError, match="missing canonical migration version 8"):
        _canonical_migration_files(tmp_path)


def test_canonical_migration_registry_rejects_unexpected_version(tmp_path):
    _write_chain(tmp_path)
    (tmp_path / "018_unapproved.sql").write_text("SELECT 18;", encoding="utf-8")
    with pytest.raises(RuntimeError, match="unexpected migration versions"):
        _canonical_migration_files(tmp_path)


def test_canonical_migration_registry_rejects_ambiguous_version(tmp_path):
    _write_chain(tmp_path, through=3)
    (tmp_path / "003_unapproved_alias.sql").write_text("SELECT 3;", encoding="utf-8")
    with pytest.raises(RuntimeError, match="ambiguous migration version 3"):
        _canonical_migration_files(tmp_path)


def test_sql_splitter_preserves_semicolons_inside_quoted_and_dollar_blocks():
    source = """
    INSERT INTO example(value) VALUES ('a;b');
    DO $$ BEGIN PERFORM 'x;y'; END $$;
    SELECT "semi;colon" FROM example;
    """
    statements = _split_sql_statements(source)
    assert len(statements) == 3
    assert "'a;b'" in statements[0]
    assert "x;y" in statements[1]
    assert '"semi;colon"' in statements[2]


def test_sql_splitter_rejects_unterminated_quote():
    with pytest.raises(ValueError, match="unterminated quote"):
        _split_sql_statements("SELECT 'unfinished;")
