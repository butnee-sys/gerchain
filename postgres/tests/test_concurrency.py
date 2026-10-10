from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
import time
import uuid

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg import sql

from postgres.migrations import apply_migrations


def _dsn() -> str:
    # psycopg accepts PostgreSQL DSNs, not SQLAlchemy driver-qualified URLs.
    value = os.environ.get("GERCHAIN_POSTGRES_DSN") or os.environ.get("GERCHAIN_DATABASE_URL") or os.environ["GERCHAIN_TEST_DATABASE_URL"]
    return value.replace("postgresql+psycopg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")


def _run_migrations() -> dict[str, object]:
    started = time.monotonic()
    with psycopg.connect(_dsn()) as conn:
        backend_pid = conn.execute("SELECT pg_backend_pid()").fetchone()[0]
        database_name = conn.info.dbname
        print(
            f"MIGRATION_CONNECTION_START pid={backend_pid} database={database_name}",
            flush=True,
        )
        apply_migrations(
            conn,
            Path(__file__).resolve().parents[1] / "migrations",
        )
        versions = conn.execute(
            "SELECT version, checksum FROM schema_version ORDER BY version"
        ).fetchall()
        elapsed = time.monotonic() - started
        print(
            f"MIGRATION_CONNECTION_DONE pid={backend_pid} database={database_name} "
            f"versions={len(versions)} elapsed_seconds={elapsed:.3f}",
            flush=True,
        )
        return {"pid": backend_pid, "database": database_name, "rows": versions}


def test_migrations_are_serialized_and_checksum_is_stable(monkeypatch):
    # EA-35.49: create a dedicated empty database so earlier tests cannot
    # accidentally pre-apply migrations and invalidate the concurrency proof.
    admin_dsn = _dsn()
    database_name = f"gerchain_migration_test_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name))
        )

    fresh_dsn = make_conninfo(admin_dsn, dbname=database_name)
    monkeypatch.setenv("GERCHAIN_POSTGRES_DSN", fresh_dsn)
    try:
        # Two independent sessions race the same truly fresh PostgreSQL database.
        # The migration runner must serialize publication and leave exactly one
        # authoritative schema_version row per version.
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(_run_migrations) for _ in range(2)]
            connection_results = [future.result(timeout=90) for future in futures]

        connection_pids = [result["pid"] for result in connection_results]
        print(
            "MIGRATION_CONCURRENCY_CONNECTIONS "
            f"pid_1={connection_pids[0]} pid_2={connection_pids[1]}",
            flush=True,
        )
        assert len(set(connection_pids)) == 2, (
            "concurrency test did not use two independent PostgreSQL backend connections: "
            f"{connection_results!r}"
        )

        with psycopg.connect(_dsn()) as conn:
            rows = conn.execute(
                "SELECT version, checksum FROM schema_version ORDER BY version"
            ).fetchall()

        versions = [row[0] for row in rows]
        assert versions == sorted(set(versions)), "duplicate schema_version publication"
        assert versions
        assert versions == list(range(1, 14)), f"schema_version history has gaps or unexpected versions: {versions}"
        assert max(versions) >= 13
        assert all(checksum for _, checksum in rows)

        # Re-run the publisher and prove both the version set and each checksum
        # are unchanged after a second complete migration pass.
        _run_migrations()
        with psycopg.connect(_dsn()) as conn:
            rows_after = conn.execute(
                "SELECT version, checksum FROM schema_version ORDER BY version"
            ).fetchall()
        assert rows_after == rows
    finally:
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            admin.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                    sql.Identifier(database_name)
                )
            )
