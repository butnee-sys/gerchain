from __future__ import annotations

from pathlib import Path

import pytest

from postgres.migrations import CANONICAL_MIGRATION_NAMES, _canonical_migration_files


def test_canonical_registry_rejects_duplicate_version_alias(tmp_path: Path) -> None:
    """A canonical version must resolve to exactly one immutable filename."""
    for name in CANONICAL_MIGRATION_NAMES.values():
        (tmp_path / name).write_text("SELECT 1;\n", encoding="utf-8")
    (tmp_path / "001_duplicate_alias.sql").write_text("SELECT 2;\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="duplicate or non-canonical migration version 1"):
        _canonical_migration_files(tmp_path)
