"""Independent PostgreSQL W3 re-performance.

Uses only psycopg and isolated tables. It intentionally does not import
GerChain schema-authority production models or persistence services.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier

import psycopg


DB_URL = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
if not DB_URL:
    raise SystemExit("GERCHAIN_TEST_DATABASE_URL is required")
PSYCOPG_DB_URL = DB_URL.replace("postgresql+psycopg://", "postgresql://", 1)


def connect():
    return psycopg.connect(PSYCOPG_DB_URL, autocommit=False)


def setup(conn, suffix: str) -> str:
    table = "w3_independent_schema_" + suffix
    with conn.cursor() as cur:
        cur.execute(
            f"CREATE TABLE {table} (schema_id text PRIMARY KEY, current_version integer NOT NULL, state_hash text NOT NULL, status text NOT NULL)"
        )
        cur.execute(f"INSERT INTO {table} VALUES ('CORE', 1, 'v1', 'ACTIVE')")
    conn.commit()
    return table


def reset_to_v1(conn_url: str, table: str) -> None:
    with psycopg.connect(conn_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE {table} SET current_version=1, state_hash='v1', status='ACTIVE' WHERE schema_id='CORE'"
            )


def upgrade(conn_url: str, table: str, upgrade_id: str, barrier: Barrier) -> str:
    with psycopg.connect(conn_url, autocommit=False) as conn:
        with conn.cursor() as cur:
            barrier.wait()
            cur.execute(f"SELECT current_version FROM {table} WHERE schema_id='CORE' FOR UPDATE")
            version = cur.fetchone()[0]
            if version != 1:
                conn.rollback()
                return "REJECTED_STALE"
            cur.execute(
                f"UPDATE {table} SET current_version=2, state_hash='v2', status='ACTIVE' WHERE schema_id='CORE' AND current_version=1"
            )
        conn.commit()
        return "APPLIED:" + upgrade_id


def same_id_upgrade(conn_url: str, table: str, barrier: Barrier) -> str:
    with psycopg.connect(conn_url, autocommit=False) as conn:
        with conn.cursor() as cur:
            barrier.wait()
            cur.execute(f"SELECT current_version FROM {table} WHERE schema_id='CORE' FOR UPDATE")
            version = cur.fetchone()[0]
            if version == 2:
                conn.rollback()
                return "IDEMPOTENT"
            cur.execute(f"UPDATE {table} SET current_version=2, state_hash='v2' WHERE schema_id='CORE' AND current_version=1")
        conn.commit()
        return "APPLIED"


def run_distinct(conn_url: str, table: str) -> None:
    reset_to_v1(conn_url, table)
    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(upgrade, conn_url, table, "u1", barrier),
            pool.submit(upgrade, conn_url, table, "u2", barrier),
        ]
        results = [future.result() for future in futures]
    assert sum(result.startswith("APPLIED:") for result in results) == 1, results
    with psycopg.connect(conn_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT current_version, state_hash FROM {table} WHERE schema_id='CORE'")
            assert cur.fetchone() == (2, "v2")


def run_same_id(conn_url: str, table: str) -> None:
    reset_to_v1(conn_url, table)
    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(same_id_upgrade, conn_url, table, barrier) for _ in range(2)]
        results = [future.result() for future in futures]
    assert sorted(results) == ["APPLIED", "IDEMPOTENT"], results


def run_rollback(conn_url: str, table: str) -> None:
    reset_to_v1(conn_url, table)
    with psycopg.connect(conn_url, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE {table} SET current_version=2, state_hash='v2' WHERE schema_id='CORE'")
        conn.rollback()
    with psycopg.connect(conn_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT current_version, state_hash FROM {table} WHERE schema_id='CORE'")
            assert cur.fetchone() == (1, "v1")


def main() -> None:
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    with connect() as conn:
        table = setup(conn, suffix)
    try:
        run_distinct(PSYCOPG_DB_URL, table)
        run_same_id(PSYCOPG_DB_URL, table)
        run_rollback(PSYCOPG_DB_URL, table)
        print("W3 independent PostgreSQL re-performance: PASS")
        print("Distinct concurrent upgrades: one authoritative successor")
        print("Same upgrade retry: idempotent")
        print("Rollback: predecessor preserved")
    finally:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(f"DROP TABLE IF EXISTS {table}")
            conn.commit()


if __name__ == "__main__":
    main()
