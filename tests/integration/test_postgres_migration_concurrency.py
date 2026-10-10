from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psycopg
import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "postgres_migration_runner.py"
DSN = os.environ.get("GERCHAIN_MIGRATION_TEST_DSN") or os.environ.get("GERCHAIN_DATABASE_URL")


@pytest.fixture(scope="module")
def dsn():
    if not DSN:
        pytest.skip("requires a real PostgreSQL DSN")
    with psycopg.connect(DSN) as conn:
        version = conn.execute("SHOW server_version").fetchone()[0]
    print(f"POSTGRES_SERVER_VERSION={version}")
    return DSN


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
    path = make_migration(tmp_path, 9901, f"CREATE TABLE {table} (id integer PRIMARY KEY);")
    # Two independent OS processes contend for the same migration lock.
    gate = tmp_path / "release"
    worker = (
        "import os,time; from pathlib import Path; "
        f"gate=Path({str(gate)!r}); "
        "deadline=time.time()+20; "
        "while not gate.exists() and time.time()<deadline: time.sleep(.01); "
        "assert gate.exists(), 'test gate timeout'; "
        "from scripts.postgres_migration_runner import apply_migration; "
        f"print(apply_migration(os.environ['GERCHAIN_DATABASE_URL'], Path({str(path)!r})))"
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
        assert conn.execute("SELECT count(*) FROM schema_version WHERE version=9901").fetchone()[0] == 1
        assert conn.execute(f"SELECT count(*) FROM information_schema.tables WHERE table_name=%s", (table,)).fetchone()[0] == 1


def test_checksum_conflict_fails_closed(dsn, tmp_path):
    original = make_migration(tmp_path, 9902, "CREATE TABLE migration_probe_checksum (id integer);")
    assert run_cli(dsn, original).returncode == 0
    changed = make_migration(tmp_path, 9902, "CREATE TABLE migration_probe_checksum (id integer, note text);", "changed")
    result = run_cli(dsn, changed)
    assert result.returncode != 0
    assert "checksum conflict" in result.stderr
    with psycopg.connect(dsn) as conn:
        checksum = conn.execute("SELECT checksum FROM schema_version WHERE version=9902").fetchone()[0]
    assert checksum == hashlib.sha256(original.read_bytes()).hexdigest()


def test_failed_migration_rolls_back_ddl_and_version_row(dsn, tmp_path):
    table = "migration_probe_rollback_" + uuid.uuid4().hex
    path = make_migration(tmp_path, 9903, f"CREATE TABLE {table} (id integer); SELECT * FROM table_that_does_not_exist_{uuid.uuid4().hex};")
    result = run_cli(dsn, path)
    assert result.returncode != 0
    with psycopg.connect(dsn) as conn:
        assert conn.execute("SELECT count(*) FROM schema_version WHERE version=9903").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_name=%s", (table,)).fetchone()[0] == 0
