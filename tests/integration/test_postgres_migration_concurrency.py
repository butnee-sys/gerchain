from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import psycopg
import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "postgres_migration_runner.py"
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


def unique_version() -> int:
    # Isolate each run because CI may retain previous migration evidence.
    return 900_000_000 + int(uuid.uuid4().hex[:8], 16)


def run_cli(dsn: str, path: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["GERCHAIN_DATABASE_URL"] = dsn
    return subprocess.run(
        [sys.executable, str(RUNNER), str(path)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=45,
    )


def make_migration(tmp_path: Path, version: int, sql: str, name: str = "probe") -> Path:
    path = tmp_path / f"{version}_{name}.sql"
    path.write_text(sql, encoding="utf-8")
    return path


def test_concurrent_first_apply_and_same_checksum_replay(dsn, tmp_path):
    table = "migration_probe_" + uuid.uuid4().hex
    path = make_migration(tmp_path, unique_version(), f"CREATE TABLE {table} (id integer PRIMARY KEY);")
    # Two independent OS processes contend for the same migration lock.
    gate = tmp_path / "release"
    worker = "\n".join(
        [
            "import os, time",
            "from pathlib import Path",
            "from scripts.postgres_migration_runner import apply_migration",
            f"gate = Path({str(gate)!r})",
            "deadline = time.time() + 20",
            "while not gate.exists() and time.time() < deadline:",
            "    time.sleep(0.01)",
            "assert gate.exists(), 'test gate timeout'",
            f"print(apply_migration(os.environ['GERCHAIN_DATABASE_URL'], Path({str(path)!r})))",
        ]
    )
    env = dict(os.environ, GERCHAIN_DATABASE_URL=dsn)
    p1 = subprocess.Popen([sys.executable, "-c", worker], cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p2 = subprocess.Popen([sys.executable, "-c", worker], cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    gate.touch()
    o1, e1 = p1.communicate(timeout=45)
    o2, e2 = p2.communicate(timeout=45)
    assert p1.returncode == 0, (o1, e1)
    assert p2.returncode == 0, (o2, e2)
    assert sorted([o1.strip(), o2.strip()]) == ["already-applied", "applied"]
    assert run_cli(dsn, path).stdout.strip().endswith("result=already-applied")
    with psycopg.connect(dsn) as conn:
        version = int(path.name.split("_", 1)[0])
        assert conn.execute("SELECT count(*) FROM schema_version WHERE version=%s", (version,)).fetchone()[0] == 1
        assert conn.execute(f"SELECT count(*) FROM information_schema.tables WHERE table_name=%s", (table,)).fetchone()[0] == 1


def test_checksum_conflict_fails_closed(dsn, tmp_path):
    table = "migration_probe_checksum_" + uuid.uuid4().hex
    original = make_migration(tmp_path, unique_version(), f"CREATE TABLE {table} (id integer);")
    assert run_cli(dsn, original).returncode == 0
    version = int(original.name.split("_", 1)[0])
    changed = make_migration(tmp_path, version, f"CREATE TABLE {table} (id integer, note text);", "changed")
    result = run_cli(dsn, changed)
    assert result.returncode != 0
    assert "checksum conflict" in result.stderr
    with psycopg.connect(dsn) as conn:
        checksum = conn.execute("SELECT checksum FROM schema_version WHERE version=9902").fetchone()[0]
    assert checksum == hashlib.sha256(original.read_bytes()).hexdigest()


def test_failed_migration_rolls_back_ddl_and_version_row(dsn, tmp_path):
    table = "migration_probe_rollback_" + uuid.uuid4().hex
    path = make_migration(tmp_path, unique_version(), f"CREATE TABLE {table} (id integer); SELECT * FROM table_that_does_not_exist_{uuid.uuid4().hex};")
    result = run_cli(dsn, path)
    assert result.returncode != 0
    with psycopg.connect(dsn) as conn:
        version = int(path.name.split("_", 1)[0])
        assert conn.execute("SELECT count(*) FROM schema_version WHERE version=%s", (version,)).fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_name=%s", (table,)).fetchone()[0] == 0

    
def test_failed_migration_releases_lock_and_same_version_can_retry(dsn, tmp_path):
    table = "migration_probe_retry_" + uuid.uuid4().hex
    version = unique_version()
    broken = make_migration(
        tmp_path,
        version,
        f"CREATE TABLE {table} (id integer); SELECT * FROM missing_retry_table_{uuid.uuid4().hex};",
        "broken",
    )
    failed = run_cli(dsn, broken)
    assert failed.returncode != 0
    with psycopg.connect(dsn) as conn:
        assert conn.execute(
            "SELECT count(*) FROM schema_version WHERE version=%s", (version,)
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_name=%s", (table,)
        ).fetchone()[0] == 0

    # Retry the same version with corrected SQL. Success proves rollback released
    # the transaction-scoped advisory lock and no failed registry row was retained.
    corrected = make_migration(
        tmp_path, version, f"CREATE TABLE {table} (id integer);", "retry"
    )
    applied = run_cli(dsn, corrected)
    assert applied.returncode == 0, (applied.stdout, applied.stderr)
    assert applied.stdout.strip().endswith("result=applied")
    with psycopg.connect(dsn) as conn:
        row = conn.execute(
            "SELECT checksum FROM schema_version WHERE version=%s", (version,)
        ).fetchone()
        assert row == (hashlib.sha256(corrected.read_bytes()).hexdigest(),)
        assert conn.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_name=%s", (table,)
        ).fetchone()[0] == 1
