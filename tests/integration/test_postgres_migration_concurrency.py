from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import uuid
from pathlib import Path

import psycopg
from psycopg.conninfo import make_conninfo
import pytest

ROOT = Path(__file__).resolve().parents[2]
DSN = (
    os.environ.get("GERCHAIN_MIGRATION_TEST_DSN")
    or os.environ.get("GERCHAIN_POSTGRES_DSN")
    or os.environ.get("GERCHAIN_DATABASE_URL")
)


@pytest.fixture(scope="module")
def dsn():
    if not DSN:
        pytest.skip("requires a real PostgreSQL DSN")
    with psycopg.connect(DSN) as conn:
        version = conn.execute("SHOW server_version").fetchone()[0]
    print(f"POSTGRES_SERVER_VERSION={version}")
    return DSN


def isolated_schema(dsn: str) -> str:
    schema = "migration_probe_" + uuid.uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as admin:
        admin.execute(f'CREATE SCHEMA "{schema}"')
    return schema


def scoped_dsn(dsn: str, schema: str) -> str:
    return make_conninfo(dsn, options=f"-c search_path={schema}")


def run_cli(dsn: str, schema: str, migration_dir: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["GERCHAIN_DATABASE_URL"] = scoped_dsn(dsn, schema)
    worker = (
        "import os; from pathlib import Path; import psycopg; "
        "from postgres.migrations import apply_migrations; "
        "conn=psycopg.connect(os.environ['GERCHAIN_DATABASE_URL']); "
        f"result=apply_migrations(conn, Path({str(migration_dir)!r})); "
        "conn.close(); print('applied' if result else 'already-applied')"
    )
    return subprocess.run(
        [sys.executable, "-c", worker],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=60,
    )


def make_migration(tmp_path: Path, sql: str) -> Path:
    directory = tmp_path / "isolated_migrations"
    directory.mkdir(exist_ok=True)
    path = directory / "001_probe.sql"
    path.write_text(sql, encoding="utf-8")
    return path


def schema_version_rows(dsn: str, schema: str):
    with psycopg.connect(scoped_dsn(dsn, schema)) as conn:
        exists = conn.execute("SELECT to_regclass('schema_version')").fetchone()[0]
        if exists is None:
            return []
        return conn.execute(
            "SELECT version, checksum, applied_at FROM schema_version ORDER BY version"
        ).fetchall()


def cleanup_schema(dsn: str, schema: str) -> None:
    with psycopg.connect(dsn, autocommit=True) as admin:
        admin.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')


def test_concurrent_first_apply_and_same_checksum_replay(dsn, tmp_path):
    schema = isolated_schema(dsn)
    table = "migration_probe_" + uuid.uuid4().hex
    path = make_migration(tmp_path, f"CREATE TABLE {table} (id integer PRIMARY KEY);")
    try:
        env = dict(os.environ, GERCHAIN_DATABASE_URL=scoped_dsn(dsn, schema))
        worker = (
            "import os, time; from pathlib import Path; import psycopg; "
            "from postgres.migrations import apply_migrations; "
            "conn=psycopg.connect(os.environ['GERCHAIN_DATABASE_URL']); "
            f"result=apply_migrations(conn, Path({str(path.parent)!r})); "
            "conn.close(); print('applied' if result else 'already-applied')"
        )
        p1 = subprocess.Popen([sys.executable, "-c", worker], cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p2 = subprocess.Popen([sys.executable, "-c", worker], cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o1, e1 = p1.communicate(timeout=60)
        o2, e2 = p2.communicate(timeout=60)
        assert p1.returncode == 0, (o1, e1)
        assert p2.returncode == 0, (o2, e2)
        assert sorted([o1.strip(), o2.strip()]) == ["already-applied", "applied"]
        assert run_cli(dsn, schema, path.parent).stdout.strip() == "already-applied"
        rows = schema_version_rows(dsn, schema)
        assert [row[0] for row in rows] == [1]
        with psycopg.connect(scoped_dsn(dsn, schema)) as conn:
            assert conn.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
                (schema, table),
            ).fetchone()[0] == 1
    finally:
        cleanup_schema(dsn, schema)


def test_checksum_conflict_fails_closed(dsn, tmp_path):
    schema = isolated_schema(dsn)
    table = "migration_probe_checksum_" + uuid.uuid4().hex
    path = make_migration(tmp_path, f"CREATE TABLE {table} (id integer);")
    try:
        first = run_cli(dsn, schema, path.parent)
        assert first.returncode == 0, (first.stdout, first.stderr)
        original_checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        path.write_text(f"CREATE TABLE {table} (id integer, note text);", encoding="utf-8")
        changed = run_cli(dsn, schema, path.parent)
        assert changed.returncode != 0
        assert "checksum conflict" in changed.stderr.lower() or "checksum" in changed.stderr.lower()
        rows = schema_version_rows(dsn, schema)
        assert len(rows) == 1 and rows[0][1] == original_checksum
        with psycopg.connect(scoped_dsn(dsn, schema)) as conn:
            columns = {
                row[0] for row in conn.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_schema=%s AND table_name=%s",
                    (schema, table),
                ).fetchall()
            }
        assert columns == {"id"}
    finally:
        cleanup_schema(dsn, schema)


def test_failed_migration_rolls_back_ddl_and_version_row(dsn, tmp_path):
    schema = isolated_schema(dsn)
    table = "migration_probe_rollback_" + uuid.uuid4().hex
    path = make_migration(
        tmp_path,
        f"CREATE TABLE {table} (id integer); SELECT * FROM missing_table_{uuid.uuid4().hex};",
    )
    try:
        result = run_cli(dsn, schema, path.parent)
        assert result.returncode != 0
        assert schema_version_rows(dsn, schema) == []
        with psycopg.connect(scoped_dsn(dsn, schema)) as conn:
            assert conn.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
                (schema, table),
            ).fetchone()[0] == 0
    finally:
        cleanup_schema(dsn, schema)


def test_failed_migration_releases_lock_and_same_version_can_retry(dsn, tmp_path):
    schema = isolated_schema(dsn)
    table = "migration_probe_retry_" + uuid.uuid4().hex
    path = make_migration(
        tmp_path,
        f"CREATE TABLE {table} (id integer); SELECT * FROM missing_retry_table_{uuid.uuid4().hex};",
    )
    try:
        failed = run_cli(dsn, schema, path.parent)
        assert failed.returncode != 0
        assert schema_version_rows(dsn, schema) == []
        with psycopg.connect(scoped_dsn(dsn, schema)) as conn:
            assert conn.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
                (schema, table),
            ).fetchone()[0] == 0

        path.write_text(f"CREATE TABLE {table} (id integer);", encoding="utf-8")
        retried = run_cli(dsn, schema, path.parent)
        assert retried.returncode == 0, (retried.stdout, retried.stderr)
        assert retried.stdout.strip() == "applied"
        rows = schema_version_rows(dsn, schema)
        assert len(rows) == 1
        assert rows[0][1] == hashlib.sha256(path.read_bytes()).hexdigest()
        with psycopg.connect(scoped_dsn(dsn, schema)) as conn:
            assert conn.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
                (schema, table),
            ).fetchone()[0] == 1
    finally:
        cleanup_schema(dsn, schema)
