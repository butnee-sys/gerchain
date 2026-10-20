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
            connection.execute("CREATE TABLE IF NOT EXISTS schema_version (version BIGINT PRIMARY KEY, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
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
            connection.execute("CREATE TABLE IF NOT EXISTS schema_version (version BIGINT PRIMARY KEY, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
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

    base_dsn = os.environ["GERCHAIN_MIGRATION_TEST_DATABASE_URL"].rsplit("/", 1)[0]
    admin_dsn = f"{base_dsn}/postgres"
    factory_database = "gerchain_factory_boot"
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(f'DROP DATABASE IF EXISTS "{factory_database}" WITH (FORCE)')
        admin.execute(f'CREATE DATABASE "{factory_database}"')
    factory_dsn = f"{base_dsn}/{factory_database}"

    monkeypatch.setenv("GERCHAIN_DATABASE_URL", factory_dsn)
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
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            admin.execute(f'DROP DATABASE IF EXISTS "{factory_database}" WITH (FORCE)')

@pytest.mark.skipif(
    not os.environ.get("GERCHAIN_MIGRATION_TEST_DATABASE_URL"),
    reason="requires a dedicated, disposable empty PostgreSQL database",
)
def test_failed_migration_rolls_back_ddl_and_schema_history() -> None:
    """DDL and schema_version publication must be one atomic migration unit."""
    dsn = os.environ["GERCHAIN_MIGRATION_TEST_DATABASE_URL"]
    with tempfile.TemporaryDirectory(prefix="gerchain-ddl-rollback-") as raw_dir:
        migration_dir = Path(raw_dir)
        migration = migration_dir / "001_failed_probe.sql"
        migration.write_text(
            "CREATE TABLE gerchain_migration_rollback_probe (id INTEGER PRIMARY KEY);\n"
            "THIS IS INTENTIONALLY INVALID SQL;\n",
            encoding="utf-8",
        )
        with psycopg.connect(dsn) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_version "
                "(version BIGINT PRIMARY KEY, checksum TEXT NOT NULL, "
                "applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            )
            connection.execute("DROP TABLE IF EXISTS gerchain_migration_rollback_probe")
            connection.execute("DELETE FROM schema_version WHERE version = 1")
            connection.commit()

            with pytest.raises(Exception):
                apply_migrations(connection, migration_dir)

        with psycopg.connect(dsn) as connection:
            assert connection.execute(
                "SELECT to_regclass('gerchain_migration_rollback_probe')"
            ).fetchone()[0] is None
            assert connection.execute(
                "SELECT version FROM schema_version WHERE version = 1"
            ).fetchall() == []

@pytest.mark.skipif(
    not os.environ.get("GERCHAIN_MIGRATION_TEST_DATABASE_URL"),
    reason="requires a dedicated, disposable PostgreSQL database",
)
def test_canonical_migration_rerun_preserves_preexisting_value_rows() -> None:
    """Snapshot real value rows before/after a canonical migration rerun."""
    from psycopg import sql
    from psycopg.conninfo import make_conninfo

    base_dsn = os.environ["GERCHAIN_MIGRATION_TEST_DATABASE_URL"]
    database_name = f"gerchain_snapshot_{os.getpid()}"
    admin_dsn = make_conninfo(base_dsn, dbname="postgres")
    snapshot_dsn = make_conninfo(base_dsn, dbname=database_name)
    migration_dir = Path(__file__).resolve().parents[2] / "postgres" / "migrations"

    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database_name)))
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))

    try:
        with psycopg.connect(snapshot_dsn) as connection:
            apply_migrations(connection, migration_dir)
            connection.execute(
                """
                INSERT INTO gerchain_ledger_accounts(account_id, currency, balance, version, updated_at)
                VALUES ('snapshot-source', 'MNT', 250, 1, now()),
                       ('snapshot-destination', 'MNT', 5, 1, now())
                """
            )
            connection.execute(
                """
                INSERT INTO gerchain_ledger_movements
                    (transaction_id, source, destination, amount, currency,
                     operation, escrow_id, integrity_hash, created_at)
                VALUES ('snapshot-tx', 'snapshot-source', 'snapshot-destination',
                        25, 'MNT', 'SETTLEMENT', NULL, repeat('c', 64), now())
                """
            )
            connection.commit()

        def snapshot() -> tuple[tuple[tuple[object, ...], ...], tuple[tuple[object, ...], ...]]:
            with psycopg.connect(snapshot_dsn) as connection:
                accounts = tuple(connection.execute(
                    """
                    SELECT account_id, currency, balance, version
                    FROM gerchain_ledger_accounts ORDER BY account_id
                    """
                ).fetchall())
                movements = tuple(connection.execute(
                    """
                    SELECT transaction_id, source, destination, amount, currency,
                           operation, escrow_id, integrity_hash
                    FROM gerchain_ledger_movements ORDER BY transaction_id
                    """
                ).fetchall())
                return accounts, movements

        before = snapshot()
        with psycopg.connect(snapshot_dsn) as connection:
            applied_again = apply_migrations(connection, migration_dir)
            assert applied_again == ()
        after = snapshot()

        assert after == before, (
            "canonical migration rerun changed existing value rows: "
            f"before={before!r}; after={after!r}"
        )
        assert len(after[0]) == 2
        assert len(after[1]) == 1
        assert sum(int(row[2]) for row in after[0]) == 255
    finally:
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            admin.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database_name)))

