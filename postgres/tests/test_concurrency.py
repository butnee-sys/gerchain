from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
import time
import uuid

import pytest

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg import sql
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL

from persistence.atomic_ledger import (
    LedgerAccountModel,
    LedgerMovementModel,
    PostgreSQLAtomicLedger,
)

from postgres.migrations import (
    CANONICAL_MIGRATION_NAMES,
    _canonical_migration_files,
    apply_migrations,
)



def test_canonical_migration_inventory_has_one_authoritative_filename_per_version():
    """Prevent selection-map drift from repeatedly reviving duplicate migration paths."""
    migration_dir = Path(__file__).resolve().parents[1] / "migrations"
    selected = _canonical_migration_files(migration_dir)
    versions = [int(path.name.split("_", 1)[0]) for path in selected]
    assert versions == list(range(1, len(CANONICAL_MIGRATION_NAMES) + 1))
    assert len(versions) == len(set(versions)), f"duplicate selected migration versions: {versions}"
    assert {
        int(path.name.split("_", 1)[0]): path.name for path in selected
    } == CANONICAL_MIGRATION_NAMES
    assert all((migration_dir / name).is_file() for name in CANONICAL_MIGRATION_NAMES.values())


def _dsn() -> str:
    # These tests are real-PostgreSQL integration tests. Skip cleanly in generic
    # unit-test jobs rather than failing because no disposable database is set.
    value = (
        os.environ.get("GERCHAIN_POSTGRES_DSN")
        or os.environ.get("GERCHAIN_DATABASE_URL")
        or os.environ.get("GERCHAIN_TEST_DATABASE_URL")
    )
    if not value:
        pytest.skip("requires a dedicated, disposable PostgreSQL test database")
    # psycopg accepts PostgreSQL DSNs, not SQLAlchemy driver-qualified URLs.
    return value.replace("postgresql+psycopg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")


def _run_migrations(runner_id: str) -> dict[str, object]:
    started = time.monotonic()
    started_wall = time.time()
    with psycopg.connect(_dsn()) as conn:
        backend_pid = conn.execute("SELECT pg_backend_pid()").fetchone()[0]
        database_name = conn.info.dbname
        print(
            f"MIGRATION_CONNECTION_START runner={runner_id} pid={backend_pid} "
            f"database={database_name} started_at={started_wall:.6f}",
            flush=True,
        )
        # The diagnostic SELECT above opens a psycopg transaction. End it before
        # the migration runner acquires its session-scoped advisory lock; the
        # runner requires a clean connection at entry.
        conn.commit()
        apply_migrations(
            conn,
            Path(__file__).resolve().parents[1] / "migrations",
        )
        versions = conn.execute(
            "SELECT version, checksum FROM schema_version ORDER BY version"
        ).fetchall()
        elapsed = time.monotonic() - started
        print(
            f"MIGRATION_CONNECTION_DONE runner={runner_id} pid={backend_pid} "
            f"database={database_name} versions={len(versions)} "
            f"ended_at={time.time():.6f} elapsed_seconds={elapsed:.3f} "
            f"rows={versions!r}",
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
            futures = [
                pool.submit(_run_migrations, "A"),
                pool.submit(_run_migrations, "B"),
            ]
            connection_results = []
            migration_errors = []
            for runner_id, future in zip(("A", "B"), futures):
                try:
                    connection_results.append(future.result(timeout=90))
                except Exception as exc:
                    migration_errors.append((runner_id, repr(exc)))
                    print(
                        f"MIGRATION_CONNECTION_ERROR runner={runner_id} error={exc!r}",
                        flush=True,
                    )

        # Inspect the authoritative table even when one runner failed.
        with psycopg.connect(fresh_dsn) as diagnostic_conn:
            diagnostic_rows = diagnostic_conn.execute(
                "SELECT version, checksum FROM schema_version ORDER BY version"
            ).fetchall()
        print(
            f"MIGRATION_SCHEMA_VERSION_ROWS database={database_name} "
            f"rows={diagnostic_rows!r}",
            flush=True,
        )
        print(
            f"MIGRATION_RUN_ORDER results={connection_results!r} errors={migration_errors!r}",
            flush=True,
        )
        if migration_errors:
            raise AssertionError(
                f"migration runners failed: {migration_errors!r}; "
                f"successful_results={connection_results!r}; "
                f"schema_version_rows={diagnostic_rows!r}"
            )

        # Both independent runners must observe the exact same published
        # migration history, not merely succeed without raising an exception.
        assert connection_results[0]["rows"] == diagnostic_rows, (
            f"runner A observed a different schema history: {connection_results[0]['rows']!r} "
            f"versus final rows {diagnostic_rows!r}"
        )
        assert connection_results[1]["rows"] == diagnostic_rows, (
            f"runner B observed a different schema history: {connection_results[1]['rows']!r} "
            f"versus final rows {diagnostic_rows!r}"
        )

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

        # Read the isolated database both concurrent migration runners used.
        # _dsn() points at the shared CI database and makes this assertion
        # order-dependent on unrelated setup if it is not migrated yet.
        with psycopg.connect(fresh_dsn) as conn:
            rows_after_concurrency = conn.execute(
                "SELECT version, checksum FROM schema_version ORDER BY version"
            ).fetchall()

        print(
            "MIGRATION_SCHEMA_VERSION_ASSERT_ROWS "
            f"database={database_name} rows={rows_after_concurrency!r}",
            flush=True,
        )
        rows = rows_after_concurrency
        versions = [row[0] for row in rows]
        assert versions == sorted(set(versions)), (
            f"duplicate schema_version publication: rows={rows!r}"
        )
        assert versions
        assert versions == list(range(1, len(CANONICAL_MIGRATION_NAMES) + 1)), f"schema_version history has gaps or unexpected versions: {versions}"
        assert max(versions) >= 16
        # Every published digest must be a full SHA-256 hex string; truthy-but-invalid
        # checksums are not sufficient evidence for a canonical migration history.
        assert all(
            len(digest) == 64 and all(ch in "0123456789abcdef" for ch in digest)
            for _, digest in rows
        ), f"invalid schema_version SHA-256 checksum(s): {rows!r}"

        # Re-run the publisher and prove both the version set and each checksum
        # are unchanged after a second complete migration pass.
        rerun_result = _run_migrations("RERUN")
        print(f"MIGRATION_RERUN_RESULT result={rerun_result!r}", flush=True)
        # The rerun connection itself must observe the exact same version/checksum
        # history, and the persisted history must remain byte-for-byte stable.
        assert rerun_result["rows"] == rows, (
            f"rerun observed changed migration history: {rerun_result['rows']!r} "
            f"versus original {rows!r}"
        )
        with psycopg.connect(fresh_dsn) as conn:
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


def test_checksum_failure_rolls_back_prior_migration_ddl_and_history(monkeypatch, tmp_path):
    """A later checksum mismatch must roll back earlier DDL and history atomically.

    Use a dedicated PostgreSQL database so other tests' canonical migration
    history cannot cause an earlier, unrelated checksum mismatch.
    """
    admin_dsn = _dsn()
    database_name = f"gerchain_checksum_rollback_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))

    fresh_dsn = make_conninfo(admin_dsn, dbname=database_name)
    migration_dir = tmp_path / "migration_bundle"
    migration_dir.mkdir()
    (migration_dir / "001_create_probe.sql").write_text(
        "CREATE TABLE migration_rollback_probe (id INTEGER);", encoding="utf-8"
    )
    (migration_dir / "002_expected.sql").write_text(
        "CREATE TABLE migration_second_probe (id INTEGER);", encoding="utf-8"
    )

    try:
        with psycopg.connect(fresh_dsn) as conn:
            conn.execute(
                """
                CREATE TABLE schema_version (
                    version INTEGER PRIMARY KEY,
                    checksum TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            conn.execute(
                "INSERT INTO schema_version(version, checksum) VALUES (2, 'deliberately-wrong-checksum')"
            )
            conn.commit()

            with pytest.raises(RuntimeError, match="Migration checksum mismatch for version 2"):
                apply_migrations(conn, migration_dir)

            probe_exists = conn.execute(
                "SELECT to_regclass('public.migration_rollback_probe')"
            ).fetchone()[0]
            second_probe_exists = conn.execute(
                "SELECT to_regclass('public.migration_second_probe')"
            ).fetchone()[0]
            versions = conn.execute(
                "SELECT version, checksum FROM schema_version ORDER BY version"
            ).fetchall()
            assert probe_exists is None
            assert second_probe_exists is None
            assert versions == [(2, "deliberately-wrong-checksum")]
    finally:
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            admin.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                    sql.Identifier(database_name)
                )
            )


def test_modified_applied_migration_is_rejected_by_checksum(monkeypatch, tmp_path):
    """Changing a migration file after publication must fail closed."""
    admin_dsn = _dsn()
    database_name = f"gerchain_checksum_mutation_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))

    fresh_dsn = make_conninfo(admin_dsn, dbname=database_name)
    migration_dir = tmp_path / "checksum_mutation_bundle"
    migration_dir.mkdir()
    migration = migration_dir / "001_create_probe.sql"
    migration.write_text(
        "CREATE TABLE checksum_probe (id INTEGER);", encoding="utf-8"
    )
    try:
        with psycopg.connect(fresh_dsn) as conn:
            apply_migrations(conn, migration_dir)
            original = conn.execute(
                "SELECT version, checksum FROM schema_version ORDER BY version"
            ).fetchall()
            assert len(original) == 1
            assert original[0][0] == 1
            conn.commit()

            migration.write_text(
                "CREATE TABLE checksum_probe (id INTEGER, changed TEXT);",
                encoding="utf-8",
            )
            with pytest.raises(
                RuntimeError, match="Migration checksum mismatch for version 1"
            ):
                apply_migrations(conn, migration_dir)

            history = conn.execute(
                "SELECT version, checksum FROM schema_version ORDER BY version"
            ).fetchall()
            columns = conn.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'checksum_probe'
                ORDER BY ordinal_position
                """
            ).fetchall()
            assert history == original
            assert [row[0] for row in columns] == ["id"]
    finally:
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            admin.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                    sql.Identifier(database_name)
                )
            )


def test_postgres_interruption_and_retry_moves_value_exactly_once(monkeypatch):
    """A rolled-back attempt moves no value; a retry and replay move it once."""
    admin_dsn = _dsn()
    database_name = f"gerchain_value_retry_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))

    fresh_dsn = make_conninfo(admin_dsn, dbname=database_name)
    monkeypatch.setenv("GERCHAIN_POSTGRES_DSN", fresh_dsn)
    conninfo = conninfo_to_dict(fresh_dsn)
    sqlalchemy_url = URL.create(
        "postgresql+psycopg",
        username=conninfo.get("user"),
        password=conninfo.get("password"),
        host=conninfo.get("host"),
        port=int(conninfo["port"]) if conninfo.get("port") else None,
        database=conninfo.get("dbname"),
    )
    engine = create_engine(sqlalchemy_url, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    tx_id = f"interruption-{uuid.uuid4().hex}"
    source = f"source-{uuid.uuid4().hex[:12]}"
    destination = f"destination-{uuid.uuid4().hex[:12]}"

    try:
        with psycopg.connect(fresh_dsn) as conn:
            apply_migrations(conn, Path(__file__).resolve().parents[1] / "migrations")

        with factory() as session:
            PostgreSQLAtomicLedger.create_account_in_transaction(session, source, "MNT", 100)
            PostgreSQLAtomicLedger.create_account_in_transaction(session, destination, "MNT", 0)
            session.commit()

        # Simulate process interruption after the in-transaction mutation but
        # before durable COMMIT: closing/rolling back must leave no partial move.
        with factory() as session:
            PostgreSQLAtomicLedger.transfer_in_transaction(
                session, tx_id, source, destination, 10, "MNT",
                operation="SETTLEMENT", escrow_id=None, integrity_hash="a" * 64,
            )
            session.rollback()

        with factory() as session:
            assert session.get(LedgerAccountModel, source).balance == 100
            assert session.get(LedgerAccountModel, destination).balance == 0
            assert session.execute(
                select(func.count()).select_from(LedgerMovementModel)
                .where(LedgerMovementModel.transaction_id == tx_id)
            ).scalar_one() == 0

        # Retry after the simulated interruption: exactly one committed move.
        with factory() as session:
            first = PostgreSQLAtomicLedger.transfer_in_transaction(
                session, tx_id, source, destination, 10, "MNT",
                operation="SETTLEMENT", escrow_id=None, integrity_hash="a" * 64,
            )
            session.commit()
            assert first["replayed"] is False

        # Simulate lost acknowledgement after commit: retry same request.
        with factory() as session:
            replay = PostgreSQLAtomicLedger.transfer_in_transaction(
                session, tx_id, source, destination, 10, "MNT",
                operation="SETTLEMENT", escrow_id=None, integrity_hash="a" * 64,
            )
            session.commit()
            assert replay["replayed"] is True

        with factory() as session:
            source_balance = session.get(LedgerAccountModel, source).balance
            destination_balance = session.get(LedgerAccountModel, destination).balance
            movement_count = session.execute(
                select(func.count()).select_from(LedgerMovementModel)
                .where(LedgerMovementModel.transaction_id == tx_id)
            ).scalar_one()
            assert (source_balance, destination_balance) == (90, 10)
            assert source_balance + destination_balance == 100
            assert movement_count == 1
    finally:
        engine.dispose()
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            admin.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                    sql.Identifier(database_name)
                )
            )

def test_migration_rerun_preserves_canonical_value_snapshot(monkeypatch):
    """Re-applying the canonical migration chain must preserve balances and movements."""
    admin_dsn = _dsn()
    database_name = f"gerchain_migration_snapshot_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))

    fresh_dsn = make_conninfo(admin_dsn, dbname=database_name)
    monkeypatch.setenv("GERCHAIN_POSTGRES_DSN", fresh_dsn)
    conninfo = conninfo_to_dict(fresh_dsn)
    sqlalchemy_url = URL.create(
        "postgresql+psycopg",
        username=conninfo.get("user"),
        password=conninfo.get("password"),
        host=conninfo.get("host"),
        port=int(conninfo["port"]) if conninfo.get("port") else None,
        database=conninfo.get("dbname"),
    )
    engine = create_engine(sqlalchemy_url, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    source = f"snapshot-source-{uuid.uuid4().hex[:8]}"
    destination = f"snapshot-dest-{uuid.uuid4().hex[:8]}"
    tx_id = f"snapshot-tx-{uuid.uuid4().hex}"
    migration_dir = Path(__file__).resolve().parents[1] / "migrations"

    try:
        with psycopg.connect(fresh_dsn) as conn:
            apply_migrations(conn, migration_dir)
        with factory() as session:
            PostgreSQLAtomicLedger.create_account_in_transaction(session, source, "MNT", 250)
            PostgreSQLAtomicLedger.create_account_in_transaction(session, destination, "MNT", 5)
            PostgreSQLAtomicLedger.transfer_in_transaction(
                session, tx_id, source, destination, 25, "MNT",
                operation="SETTLEMENT", escrow_id=None, integrity_hash="b" * 64,
            )
            session.commit()

        def snapshot():
            with factory() as session:
                accounts = tuple(
                    (r.account_id, r.currency, int(r.balance), int(r.version))
                    for r in session.execute(
                        select(LedgerAccountModel).order_by(LedgerAccountModel.account_id)
                    ).scalars()
                )
                movements = tuple(
                    (r.transaction_id, r.source, r.destination, int(r.amount),
                     r.currency, r.operation, r.escrow_id, r.integrity_hash)
                    for r in session.execute(
                        select(LedgerMovementModel).order_by(LedgerMovementModel.transaction_id)
                    ).scalars()
                )
                return accounts, movements

        before = snapshot()
        with psycopg.connect(fresh_dsn) as conn:
            apply_migrations(conn, migration_dir)
        after = snapshot()

        assert after == before, (
            "canonical migration rerun changed value truth: "
            f"before={before!r}, after={after!r}"
        )
        assert len(after[1]) == 1
        assert sum(row[2] for row in after[0]) == 255
    finally:
        engine.dispose()
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            admin.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                    sql.Identifier(database_name)
                )
            )



def test_postgres_rejects_invalid_escrow_state_via_named_check_constraint(monkeypatch):
    """The database error for NOT_A_STATE is expected, not a migration failure."""
    admin_dsn = _dsn()
    database_name = f"gerchain_invalid_state_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))

    fresh_dsn = make_conninfo(admin_dsn, dbname=database_name)
    monkeypatch.setenv("GERCHAIN_POSTGRES_DSN", fresh_dsn)
    try:
        with psycopg.connect(fresh_dsn) as conn:
            apply_migrations(conn, Path(__file__).resolve().parents[1] / "migrations")
            with pytest.raises(psycopg.errors.CheckViolation) as exc_info:
                conn.execute(
                    """
                    INSERT INTO escrows (
                        id, sender_address, receiver_address, amount, state,
                        refund_destination, currency, version, created_at, updated_at
                    ) VALUES (
                        'invalid-state-test', 'sender', 'receiver', 100,
                        'NOT_A_STATE', 'sender', 'MNT', 0, now(), now()
                    )
                    """
                )
            assert exc_info.value.diag.constraint_name == "escrows_state_canonical_check"
            conn.rollback()
    finally:
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            admin.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database_name)))
