from __future__ import annotations

import hashlib
from contextlib import contextmanager, nullcontext
from pathlib import Path

import psycopg.sql
from sqlalchemy import text


MIGRATION_LOCK_KEY = 73546501

# Version 004 previously shipped with explicit BEGIN/COMMIT wrappers. Keep its
# historical checksum accepted so existing databases can migrate to the
# runner-compatible source without rewriting schema history.
FROZEN_CHECKSUMS = {
    1: {"538e0f5132ec775ec8963a2a72072dd00e81afa37383a6c5f6a8f54259716a31"},
    2: {"0531b1b8ecd29118a6755538a701ab8dd751425c431d15f4fa50b400dd8dfcc7"},
    3: {
        "50c86703a173d5faeabb2276a50fa165938abb3fc02bcdb13fa56255833227a9",
        # Historical checksum observed in existing production-smoke databases.
        "15caac76ff599ec1a83091f2d7b3f9bb428f9ad04474f215df1ae9d39611a13e",
    },
    4: {
        "0d5d063a1d35fbb79bef3023e8b02e06e76776c0af5da41b843fb702b702cf57",
        # Historical checksum observed in PostgreSQL production evidence.
        "55a9ab0753356174ea6427d4c746958a563afb202265d170dae48df13afb8c9a",
    },
    5: {"ecfc4306afb3b7ccde65902487f0702a6697ac343bced4534f624d134984effb"},
    6: {"68fee98cb004ce99fd7acf8cfd29e305cd0f770cf7992f4426b95e108e4265e9"},
    7: {"d7e97c874b8edf58d6c08a41f3b9f245d235485a7a942565fc9d73312a1a5b55"},
    8: {"ffee1c1cedaa59d7b40c75b67fe035a11e4f3cdfd9c9079a62c78a8016c2abe3"},
    9: {"ff2c383cddc8e9d6b5d399e2ce043cdf629de7864c8ba8cafb5a5160e947a28a"},
    10: {
        "282bdd44d550161052f5a1c99d563e3832c4cbba558854988171fc9179b676c6",
        "b019fb3f29ba1926fe1806f33aa344013ed38c36aefb374baa4feced220dbf3b",
    },
    11: {"aa3b8fe4d39a61e5ba3f12a3b70b14b5a560e2bdb988cfeb068c2a8fec19494a"},
}

LEGACY_CHECKSUMS = {
    # Version 001 was historically recorded from postgres/schema/001_concurrency.sql.
    # The migration runner now owns that schema history; accept the known legacy
    # digest so existing databases can migrate without rewriting version 1.
    1: {
        "6eea24dae8b3ac9aa9413a32da1617250f14725bdb19f50e5d8300308ad173d4",
        "538e0f5132ec775ec8963a2a72072dd00e81afa37383a6c5f6a8f54259716a31",
        "ab6838b3e69a9a9faa28bdd82c98fe579921763be8b5dd56e1c686b77c098596",
    },
    3: {"50c86703a173d5faeabb2276a50fa165938abb3fc02bcdb13fa56255833227a9"},
    4: {
        "729c586234c0b630cce6edd9feab694f4d589dcb5e9321e44f7d22ab556799a0",
        "0d5d063a1d35fbb79bef3023e8b02e06e76776c0af5da41b843fb702b702cf57",
    },
    5: {"ecfc4306afb3b7ccde65902487f0702a6697ac343bced4534f624d134984effb"},
}


def checksum(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


@contextmanager
def _native_migration_transaction(conn):
    """Serialize native psycopg migration runners across the whole migration run."""
    if _connection_in_transaction(conn):
        raise RuntimeError("migration runner requires a clean psycopg transaction")

    # Use a session-level advisory lock, explicitly committed before opening the
    # migration transaction.  This makes the serialization boundary independent
    # of transaction nesting and prevents two native runners from ever entering
    # the schema-version read/apply/record section concurrently.
    conn.execute("SELECT pg_advisory_lock(%s)", (MIGRATION_LOCK_KEY,))
    conn.commit()
    try:
        with conn.transaction():
            yield
    finally:
        conn.execute("SELECT pg_advisory_unlock(%s)", (MIGRATION_LOCK_KEY,))
        conn.commit()

@contextmanager
def _sqlalchemy_migration_transaction(conn):
    """Serialize SQLAlchemy migration callers, including pre-open transactions."""
    if conn.in_transaction():
        conn.execute(text("SELECT pg_advisory_xact_lock(%s)" % MIGRATION_LOCK_KEY))
        yield
        return
    with conn.begin():
        conn.execute(text("SELECT pg_advisory_xact_lock(%s)" % MIGRATION_LOCK_KEY))
        yield


def _transaction(conn):
    """Return a real transaction context for SQLAlchemy or native psycopg."""
    if hasattr(conn, "exec_driver_sql") and hasattr(conn, "begin"):
        return _sqlalchemy_migration_transaction(conn)
    if hasattr(conn, "transaction"):
        return _native_migration_transaction(conn)
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
        8: "008_ea35_idempotency_compat.sql",
        9: "009_canonical_movement_integrity_hardening.sql",
        10: "010_canonical_evidence_constraints.sql",
        11: "011_ea35_canonical_schema_finalization.sql",
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
                preferred[version] = candidates[0]
            elif not candidates:
                # A preferred historical version has no physical migration here.
                continue
            else:
                raise RuntimeError(
                    f"Preferred migration {preferred_name} is missing and "
                    f"version {version} has multiple active candidates"
                )
        elif len(candidates) == 1:
            preferred[version] = candidates[0]
        else:
            raise RuntimeError(
                f"Unresolved duplicate migration version {version}: "
                + ", ".join(p.name for p in candidates)
            )

    # Serialize concurrent migration runners before any migration transaction is opened.
    # Native psycopg uses a session advisory lock; SQLAlchemy uses a transaction-scoped lock.
    migration_context = (
        _native_migration_transaction(conn)
        if hasattr(conn, "transaction") and not hasattr(conn, "exec_driver_sql")
        else _transaction(conn)
    )
    try:
        with migration_context:
            # Use psycopg-native positional parameters for both SQLAlchemy's
            # exec_driver_sql path and native psycopg. SQLAlchemy does not
            # translate :name placeholders when exec_driver_sql() is used.
            if hasattr(conn, "exec_driver_sql"):
                _execute(conn, "SELECT pg_advisory_xact_lock(%s)", (MIGRATION_LOCK_KEY,))
            _execute(
                conn,
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version BIGINT PRIMARY KEY,
                    checksum TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """,
            )
            _execute(conn, "LOCK TABLE schema_version IN ACCESS EXCLUSIVE MODE")
            rows = _execute(
                conn,
                "SELECT version, checksum FROM schema_version ORDER BY version",
            ).fetchall()
            applied = {int(row[0]): row[1] for row in rows}

            for version in sorted(preferred):
                migration = preferred[version]
                sql = migration.read_text(encoding="utf-8")
                digest = checksum(sql)
                accepted_digests = set(LEGACY_CHECKSUMS.get(version, set()))
                accepted_digests.update(FROZEN_CHECKSUMS.get(version, set()))

                if version in applied:
                    if applied[version] != digest and applied[version] not in accepted_digests:
                        raise RuntimeError(
                            f"Migration checksum mismatch for version {version}: "
                            f"applied={applied[version]} expected={digest}"
                        )
                    continue

                migration_sql = sql.replace("BEGIN;", "").replace("COMMIT;", "")
                _execute(conn, migration_sql)
                # Concurrent runners may both finish the same migration body
                # after serialized lock handoff; recording is therefore race-safe.
                _execute(
                    conn,
                    """
                    INSERT INTO schema_version(version, checksum)
                    VALUES (%s, %s)
                    ON CONFLICT (version) DO UPDATE
                    SET checksum = EXCLUDED.checksum
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
    except Exception:
        if hasattr(conn, "rollback"):
            conn.rollback()
        raise
