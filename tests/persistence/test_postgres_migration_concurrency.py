from __future__ import annotations

import os
import tempfile
import threading
from pathlib import Path

import psycopg
import pytest

from postgres.migrations import apply_migrations


@pytest.mark.skipif(
    not os.environ.get("GERCHAIN_MIGRATION_TEST_DATABASE_URL"),
    reason="requires a dedicated, disposable empty PostgreSQL database",
)
def test_two_connections_publish_same_migration_version_once() -> None:
    """Real PostgreSQL race test; never point this at a shared production database."""
    dsn = os.environ["GERCHAIN_MIGRATION_TEST_DATABASE_URL"]
    with tempfile.TemporaryDirectory(prefix="gerchain-migrations-") as raw_dir:
        migration_dir = Path(raw_dir)
        migration = migration_dir / "001_concurrency_probe.sql"
        migration.write_text(
            "CREATE TABLE IF NOT EXISTS gerchain_migration_concurrency_probe "
            "(id INTEGER PRIMARY KEY)",
            encoding="utf-8",
        )
        with psycopg.connect(dsn) as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
            connection.execute("DROP TABLE IF EXISTS gerchain_migration_concurrency_probe")
            connection.execute("DELETE FROM schema_version WHERE version = 1")
            connection.commit()

        barrier = threading.Barrier(2)
        results: list[tuple[int, ...]] = []
        errors: list[BaseException] = []

        def run() -> None:
            try:
                with psycopg.connect(dsn) as connection:
                    barrier.wait(timeout=10)
                    results.append(apply_migrations(connection, migration_dir))
            except BaseException as exc:
                errors.append(exc)

        threads = [threading.Thread(target=run) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        assert all(not thread.is_alive() for thread in threads), "migration runner deadlocked"
        assert not errors, repr(errors)
        assert sorted(len(result) for result in results) == [0, 1]

        with psycopg.connect(dsn) as connection:
            rows = connection.execute(
                "SELECT version FROM schema_version WHERE version = 1"
            ).fetchall()
            assert rows == [(1,)]
            assert connection.execute(
                "SELECT to_regclass('gerchain_migration_concurrency_probe')"
            ).fetchone()[0] is not None


@pytest.mark.skipif(
    not os.environ.get("GERCHAIN_MIGRATION_TEST_DATABASE_URL"),
    reason="requires a dedicated, disposable empty PostgreSQL database",
)
def test_checksum_mismatch_rolls_back_schema_and_history() -> None:
    """A changed migration must not execute DDL or mutate the stored history."""
    dsn = os.environ["GERCHAIN_MIGRATION_TEST_DATABASE_URL"]
    with tempfile.TemporaryDirectory(prefix="gerchain-checksum-") as raw_dir:
        migration_dir = Path(raw_dir)
        migration = migration_dir / "001_checksum_probe.sql"
        migration.write_text(
            "CREATE TABLE IF NOT EXISTS gerchain_migration_checksum_probe "
            "(id INTEGER PRIMARY KEY)",
            encoding="utf-8",
        )
        with psycopg.connect(dsn) as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
            connection.execute("DROP TABLE IF EXISTS gerchain_migration_checksum_probe")
            connection.execute("DELETE FROM schema_version WHERE version = 1")
            connection.commit()
            assert apply_migrations(connection, migration_dir) == (1,)

        with psycopg.connect(dsn) as connection:
            before = connection.execute(
                "SELECT version, checksum FROM schema_version WHERE version = 1"
            ).fetchall()
            assert connection.execute(
                "SELECT to_regclass('gerchain_migration_checksum_probe')"
            ).fetchone()[0] is not None
            connection.commit()

            migration.write_text(
                "CREATE TABLE gerchain_migration_checksum_probe_changed "
                "(id INTEGER PRIMARY KEY)",
                encoding="utf-8",
            )
            with pytest.raises(RuntimeError, match="checksum mismatch"):
                apply_migrations(connection, migration_dir)

            after = connection.execute(
                "SELECT version, checksum FROM schema_version WHERE version = 1"
            ).fetchall()
            assert after == before
            assert connection.execute(
                "SELECT to_regclass('gerchain_migration_checksum_probe')"
            ).fetchone()[0] is not None
            assert connection.execute(
                "SELECT to_regclass('gerchain_migration_checksum_probe_changed')"
            ).fetchone()[0] is None


@pytest.mark.skipif(
    not os.environ.get("GERCHAIN_MIGRATION_TEST_DATABASE_URL"),
    reason="requires a dedicated, disposable empty PostgreSQL database",
)
def test_production_factory_boots_with_canonical_ledger_authority(monkeypatch) -> None:
    """Real PostgreSQL boot check for the exact production factory path."""
    from production_entrypoint import build_production_runtime

    monkeypatch.setenv("GERCHAIN_DATABASE_URL", os.environ["GERCHAIN_MIGRATION_TEST_DATABASE_URL"])
    monkeypatch.setenv("GERCHAIN_ESCROW_ID", "factory-boot-escrow")
    monkeypatch.setenv("GERCHAIN_ESCROW_AMOUNT", "1")
    monkeypatch.setenv("GERCHAIN_CURRENCY", "MNT")
    monkeypatch.setenv("GERCHAIN_WITNESS_ID", "factory-boot-witness")

    runtime, engine = build_production_runtime()
    try:
        assert runtime.is_canonical_ledger_authoritative
        assert runtime.runtime_mode == "production-postgresql"
        assert runtime.escrow_engine.escrow_id == "factory-boot-escrow"
    finally:
        engine.dispose()
