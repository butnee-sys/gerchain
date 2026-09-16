"""Independent PostgreSQL W2 re-performance.

This test intentionally uses only psycopg and an isolated database schema.
It does not import GerChain production models, persistence services, or
production fingerprint helpers. The purpose is to independently reproduce
PostgreSQL transactional behavior for the frozen W2 C2/C6 semantics.
"""

from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier

import psycopg


DB_URL = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
if not DB_URL:
    raise SystemExit("GERCHAIN_TEST_DATABASE_URL is required")


def digest(state: dict) -> str:
    payload = json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def connect():
    return psycopg.connect(DB_URL, autocommit=False)


def setup(conn, suffix: str) -> tuple[str, str]:
    table = "w2_independent_liquidity_" + suffix
    ledger = "w2_independent_ledger_" + suffix
    with conn.cursor() as cur:
        cur.execute(
            f"CREATE TABLE {table} (pool_id text PRIMARY KEY, capacity bigint NOT NULL, consumed bigint NOT NULL)"
        )
        cur.execute(
            f"CREATE TABLE {ledger} (operation_id text PRIMARY KEY, amount bigint NOT NULL)"
        )
        cur.execute(f"INSERT INTO {table} VALUES ('POOL', 2000000, 0)")
    conn.commit()
    return table, ledger


def concurrent_consumer(conn_url: str, table: str, ledger: str, op_id: str, barrier: Barrier) -> bool:
    with psycopg.connect(conn_url, autocommit=False) as conn:
        try:
            with conn.cursor() as cur:
                barrier.wait()
                cur.execute(f"SELECT capacity, consumed FROM {table} WHERE pool_id='POOL' FOR UPDATE")
                capacity, consumed = cur.fetchone()
                amount = 1_500_000
                if consumed + amount > capacity:
                    conn.rollback()
                    return False
                cur.execute(f"UPDATE {table} SET consumed=consumed+%s WHERE pool_id='POOL'", (amount,))
                cur.execute(f"INSERT INTO {ledger}(operation_id, amount) VALUES (%s, %s)", (op_id, amount))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise


def run_c2(conn_url: str, table: str, ledger: str, suffix: str) -> None:
    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(concurrent_consumer, conn_url, table, ledger, f"A-{suffix}", barrier),
            pool.submit(concurrent_consumer, conn_url, table, ledger, f"B-{suffix}", barrier),
        ]
        results = [future.result() for future in futures]

    assert sum(results) == 1, results
    with psycopg.connect(conn_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT capacity, consumed FROM {table} WHERE pool_id='POOL'")
            capacity, consumed = cur.fetchone()
            cur.execute(f"SELECT count(*), coalesce(sum(amount), 0) FROM {ledger}")
            count, committed = cur.fetchone()
    assert committed == 1_500_000
    assert consumed == 1_500_000
    assert committed <= capacity
    assert count == 1


def run_c6(conn_url: str, table: str, suffix: str) -> None:
    with psycopg.connect(conn_url, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT capacity, consumed FROM {table} WHERE pool_id='POOL'")
            capacity, consumed = cur.fetchone()
            decision = {
                "pool_id": "POOL",
                "capacity": capacity,
                "consumed": consumed,
                "amount": 1_000_000,
            }
            decision_hash = digest(decision)
            cur.execute(f"UPDATE {table} SET consumed=500000 WHERE pool_id='POOL'")
        conn.commit()

    with psycopg.connect(conn_url, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT capacity, consumed FROM {table} WHERE pool_id='POOL' FOR UPDATE")
            capacity, consumed = cur.fetchone()
            current = {
                "pool_id": "POOL",
                "capacity": capacity,
                "consumed": consumed,
                "amount": 1_000_000,
            }
            assert digest(current) != decision_hash
            stale_rejected = True
            if digest(current) == decision_hash:
                cur.execute(f"UPDATE {table} SET consumed=consumed+1000000 WHERE pool_id='POOL'")
                stale_rejected = False
        conn.rollback()
    assert stale_rejected


def main() -> None:
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    with connect() as conn:
        table, ledger = setup(conn, suffix)

    try:
        run_c2(DB_URL, table, ledger, suffix)
        run_c6(DB_URL, table, suffix)
        print("W2 independent PostgreSQL re-performance: PASS")
        print("C2: concurrent distinct consumers -> one commit, total=1500000, over-allocation=False")
        print("C6: changed PostgreSQL state -> stale decision rejected before mutation")
    finally:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(f"DROP TABLE IF EXISTS {ledger}")
                cur.execute(f"DROP TABLE IF EXISTS {table}")
            conn.commit()


if __name__ == "__main__":
    main()
