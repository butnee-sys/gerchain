from __future__ import annotations

import hashlib
from contextlib import nullcontext
from pathlib import Path

import psycopg.sql
from sqlalchemy import text


MIGRATION_LOCK_KEY = 73546501

# Version 004 previously shipped with explicit BEGIN/COMMIT wrappers. Keep its
# historical checksum accepted so existing databases can migrate to the
# runner-compatible source without rewriting schema history.
LEGACY_CHECKSUMS = {
    # Version 001 was historically recorded from postgres/schema/001_concurrency.sql.
    # The migration runner now owns that schema history; accept the known legacy
    # digest so existing databases can migrate without rewriting version 1.
    1: {"6eea24dae8b3ac9aa9413a32da1617250f14725bdb19f50e5d8300308ad173d4"},
    4: {"729c586234c0b630cce6edd9feab694f4d589dcb5e9321e44f7d22ab556799a0"},
}


def checksum(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def _transaction(conn):
    """Support both SQLAlchemy and native psycopg connections."""
    if hasattr(conn, "in_transaction"):
        return nullcontext() if conn.in_transaction() else conn.begin()
    if hasattr(conn, "begin"):
        return conn.begin()
    if hasattr(conn, "transaction"):
        return conn.transaction()
    return nullcontext()


def _execute(conn, sql: str, params=None):
    # Non-parameterized DDL/PLpgSQL may contain literal percent signs.
    # Avoid psycopg's pyformat parser when there are no parameters.
    if hasattr(conn, "exec_driver_sql"):
        if params is None:
            # SQLAlchemy's PostgreSQL driver still interprets literal % signs
            # when using exec_driver_sql. text() preserves PL/pgSQL format
            # strings such as format('%I', ...) as literal SQL.
            return conn.execute(text(sql))
        return conn.exec_driver_sql(sql, params)
    if params is None:
        # Native psycopg parses % as a placeholder even for literal DDL.
        # SQL() marks the migration as literal SQL without changing its source text.
        return conn.execute(psycopg.sql.SQL(sql))
    return conn.execute(sql, params)


def _connection_in_transaction(conn) -> bool:
    value = getattr(conn, "in_transaction", False)
    return value() if callable(value) else bool(value)


def apply_migrations(conn, migration_dir: str | Path) -> None:
    """Apply migrations atomically for SQLAlchemy or native psycopg connections."""
    path = Path(migration_dir)
    files = sorted(path.glob("*.sql"))
    # A few early canonical migrations were shipped under the same numeric
    # version before the migration history was frozen. Treat those files as
    # historical aliases: one deterministic file is applied on a fresh
    # database, while an already-applied checksum from any alias remains
    # accepted.
    preferred_names = {
        2: "002_canonical_production.sql",
        5: "005_canonical_production.sql",
        6: "006_canonical_production.sql",
        7: "007_canonical_production.sql",
    }
    versions: dict[int, list[Path]] = {}
    for migration in files:
        version = int(migration.name.split("_", 1)[0])
        versions.setdefault(version, []).append(migration)

    preferred: dict[int, Path] = {}
    for version, candidates in versions.items():
        preferred_name = preferred_names.get(version)
        if preferred_name:
            selected = next((p for p in candidates if p.name == preferred_name), None)
            if selected is not None:
                preferred[version] = selected
            elif len(candidates) == 1:
                # The preferred alias may be absent on a rebased migration history.
                preferred[version] = candidates[0]
            elif not candidates:
                # A preferred historical version has no physical migration here.
                continue
            else:
                raise RuntimeError(
                    f"Preferred migration {preferred_name} is missing and "
                    f"version {version} has multiple candidates"
                )
        elif len(candidates) == 1:
            preferred[version] = candidates[0]
        else:
            raise RuntimeError(
                f"Unresolved duplicate migration version {version}: "
                + ", ".join(p.name for p in candidates)
            )

    # Serialize migration runners inside the migration transaction itself.
    # Transaction-scoped advisory locking prevents two independent PostgreSQL
    # connections from racing on schema_version while also avoiding an
    # implicit-transaction/session-lock split.
    with _transaction(conn):
        _execute(conn, "SELECT pg_advisory_xact_lock(%s)", (MIGRATION_LOCK_KEY,))
        _execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version BIGINT PRIMARY KEY,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        rows = _execute(
            conn,
            "SELECT version, checksum FROM schema_version ORDER BY version",
        ).fetchall()
        applied = {int(row[0]): row[1] for row in rows}

        for version in sorted(preferred):
            migration = preferred[version]
            sql = migration.read_text(encoding="utf-8")
            digest = checksum(sql)
            accepted_digests = {
                checksum(candidate.read_text(encoding="utf-8"))
                for candidate in versions[version]
            }
            accepted_digests.update(LEGACY_CHECKSUMS.get(version, set()))

            if version in applied:
                if applied[version] not in accepted_digests:
                    raise RuntimeError(
                        f"Migration checksum mismatch for version {version}"
                    )
                continue

            migration_sql = sql.replace("BEGIN;", "").replace("COMMIT;", "")
            _execute(conn, migration_sql)
            _execute(
                conn,
                """
                INSERT INTO schema_version(version, checksum)
                VALUES (%s, %s)
                ON CONFLICT (version) DO NOTHING
                """,
                (version, digest),
            )
            recorded = _execute(
                conn,
                "SELECT checksum FROM schema_version WHERE version = %s",
                (version,),
            ).fetchone()
            if recorded is None or recorded[0] != digest:
                raise RuntimeError(
                    f"Migration checksum mismatch for version {version}"
                )
