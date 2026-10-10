"""Serialized, checksummed PostgreSQL migration runner.

The 13-file canonical chain is explicit because historical aliases coexist in
this directory. Schema DDL, checksum verification, and schema_version publication
run in one transaction under a transaction-scoped advisory lock.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from psycopg import Connection

_MIGRATION_LOCK_KEY = 731946205821
_CANONICAL_FILES = (
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
)


def checksum(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _canonical_migration_files(migration_dir: Path) -> list[Path]:
    directory = Path(migration_dir)
    if not directory.is_dir():
        raise FileNotFoundError(f"migration directory does not exist: {directory}")
    files = list(directory.glob("*.sql"))
    by_version: dict[int, list[Path]] = {}
    for path in files:
        match = re.match(r"^(\d+)_", path.name)
        if match:
            by_version.setdefault(int(match.group(1)), []).append(path)
    # Reject unknown ambiguous versions. Historical aliases for known canonical
    # versions are permitted only when the canonical filename is present.
    selected: list[Path] = []
    for version, canonical_name in enumerate(_CANONICAL_FILES, start=1):
        candidates = by_version.get(version, [])
        canonical = directory / canonical_name
        if not canonical.is_file():
            raise RuntimeError(f"missing canonical migration version {version}: {canonical_name}")
        if len(candidates) > 1 and canonical not in candidates:
            raise RuntimeError(f"ambiguous migration version {version}: {[p.name for p in candidates]}")
        selected.append(canonical)
    unexpected = sorted(set(by_version) - set(range(1, len(_CANONICAL_FILES) + 1)))
    if unexpected:
        raise RuntimeError(f"unexpected migration versions: {unexpected}")
    return selected


def _split_sql_statements(source: str) -> list[str]:
    """Split PostgreSQL SQL without splitting quoted strings or dollar blocks."""
    statements: list[str] = []
    buffer: list[str] = []
    single = double = False
    dollar_tag: str | None = None
    i = 0
    while i < len(source):
        if dollar_tag is not None:
            if source.startswith(dollar_tag, i):
                buffer.append(dollar_tag)
                i += len(dollar_tag)
                dollar_tag = None
            else:
                buffer.append(source[i])
                i += 1
            continue
        if not single and not double and source[i] == "$":
            match = re.match(r"\$[A-Za-z_][A-Za-z0-9_]*\$|\$\$", source[i:])
            if match:
                dollar_tag = match.group(0)
                buffer.append(dollar_tag)
                i += len(dollar_tag)
                continue
        char = source[i]
        if char == "'" and not double:
            if single and i + 1 < len(source) and source[i + 1] == "'":
                buffer.extend(("'", "'"))
                i += 2
                continue
            single = not single
        elif char == '"' and not single:
            if double and i + 1 < len(source) and source[i + 1] == '"':
                buffer.extend(('"', '"'))
                i += 2
                continue
            double = not double
        if char == ";" and not single and not double:
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
        else:
            buffer.append(char)
        i += 1
    tail = "".join(buffer).strip()
    if tail:
        statements.append(tail)
    if single or double or dollar_tag is not None:
        raise ValueError("unterminated quote in migration SQL")
    return statements


def apply_migrations(connection: Connection, migration_dir: Path) -> tuple[int, ...]:
    if connection.closed:
        raise ValueError("migration connection must be open")
    if connection.info.transaction_status != 0:
        raise RuntimeError("migration runner requires a clean connection with no active transaction")
    directory = Path(migration_dir)
    canonical_first = directory / _CANONICAL_FILES[0]
    if canonical_first.is_file():
        selected = _canonical_migration_files(directory)
    else:
        # Isolated test/migration bundles may use a generic sequential chain.
        # Production always uses the explicit 13-file canonical chain above.
        candidates = sorted(directory.glob("*.sql"))
        if not candidates:
            raise RuntimeError("no SQL migrations found")
        versions: dict[int, list[Path]] = {}
        for path in candidates:
            match = re.match(r"^(\d+)_", path.name)
            if not match:
                raise RuntimeError(f"invalid migration filename: {path.name}")
            versions.setdefault(int(match.group(1)), []).append(path)
        duplicates = [version for version, paths in versions.items() if len(paths) > 1]
        if duplicates:
            raise RuntimeError(f"ambiguous migration version {min(duplicates)}")
        expected = list(range(1, max(versions) + 1))
        if sorted(versions) != expected:
            raise RuntimeError(f"migration versions contain gaps: {sorted(versions)}")
        selected = [versions[version][0] for version in expected]
    applied_now: list[int] = []
    # Advisory lock, schema changes, and history publication share one transaction.
    with connection.transaction():
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (_MIGRATION_LOCK_KEY,))
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        for version, path in enumerate(selected, start=1):
            source = path.read_text(encoding="utf-8")
            if not source.strip():
                raise ValueError(f"empty migration is not allowed: {path.name}")
            digest = checksum(source)
            row = connection.execute(
                "SELECT checksum FROM schema_version WHERE version = %s",
                (version,),
            ).fetchone()
            if row is not None:
                if row[0] != digest:
                    raise RuntimeError(f"Migration checksum mismatch for version {version}: {path.name}")
                continue
            for statement in _split_sql_statements(source):
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_version(version, checksum) VALUES (%s, %s)",
                (version, digest),
            )
            applied_now.append(version)
    return tuple(applied_now)


__all__ = ["apply_migrations", "checksum", "_canonical_migration_files", "_split_sql_statements"]
