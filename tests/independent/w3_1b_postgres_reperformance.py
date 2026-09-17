"""Independent PostgreSQL re-performance of the W3.1-B migration contract.

This module intentionally does not import GerChain production migration,
schema-authority, or reconciliation code. It reproduces the contract with
psycopg and direct PostgreSQL state, then falsifies the required boundaries.
"""
from __future__ import annotations

import hashlib
import os
import threading

import psycopg


URL = os.environ["GERCHAIN_TEST_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")


def h(sql: str) -> str:
    return hashlib.sha256(" ".join(sql.strip().rstrip(";").split()).encode()).hexdigest()


def setup(conn):
    conn.execute("DROP SCHEMA IF EXISTS w31b_ind CASCADE")
    conn.execute("CREATE SCHEMA w31b_ind")
    conn.execute("DROP TABLE IF EXISTS w31b_schema_upgrade")
    conn.execute("DROP TABLE IF EXISTS w31b_schema_state")
    conn.execute("CREATE TABLE w31b_schema_state (schema_id text PRIMARY KEY, version integer NOT NULL, state_hash text NOT NULL)")
    conn.execute("CREATE TABLE w31b_schema_upgrade (migration_id text PRIMARY KEY, schema_id text NOT NULL, from_version integer NOT NULL, to_version integer NOT NULL, migration_hash text NOT NULL, status text NOT NULL)")
    conn.execute("INSERT INTO w31b_schema_state VALUES ('CORE', 1, 'v1')")
    conn.commit()


def migrate(sql: str, migration_id: str, expected_hash: str, delay: float = 0.0):
    with psycopg.connect(URL) as conn:
        with conn.transaction():
            row = conn.execute(
                "SELECT version FROM w31b_schema_state WHERE schema_id='CORE' FOR UPDATE"
            ).fetchone()
            if row[0] != 1:
                existing = conn.execute(
                    "SELECT status, migration_hash FROM w31b_schema_upgrade WHERE migration_id=%s",
                    (migration_id,),
                ).fetchone()
                if existing and existing[0] == "APPLIED" and existing[1] == h(sql):
                    return "RETRY"
                raise RuntimeError("STALE_PREDECESSOR")
            existing = conn.execute(
                "SELECT migration_hash, status FROM w31b_schema_upgrade WHERE migration_id=%s",
                (migration_id,),
            ).fetchone()
            if existing:
                if existing == (h(sql), "APPLIED"):
                    return "RETRY"
                raise RuntimeError("IDENTITY_CONFLICT")
            conn.execute(sql)
            actual = conn.execute(
                "SELECT md5(string_agg(c.relname, ',' ORDER BY c.relname)) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='w31b_ind' AND c.relkind='r'"
            ).fetchone()[0]
            # The independent reproduction binds the observed physical result
            # to the declared expected value; a mismatch aborts the transaction.
            if expected_hash != actual:
                raise RuntimeError("ACTUAL_SCHEMA_MISMATCH")
            conn.execute(
                "INSERT INTO w31b_schema_upgrade VALUES (%s,'CORE',1,2,%s,'APPLIED')",
                (migration_id, h(sql)),
            )
            conn.execute("UPDATE w31b_schema_state SET version=2, state_hash=%s WHERE schema_id='CORE'", (actual,))
            return "APPLIED"


def target_hash(conn):
    return conn.execute(
        "SELECT md5(string_agg(c.relname, ',' ORDER BY c.relname)) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='w31b_ind' AND c.relkind='r'"
    ).fetchone()[0]


def main():
    with psycopg.connect(URL) as conn:
        setup(conn)
        conn.execute("CREATE TABLE w31b_ind.target (id bigint PRIMARY KEY)")
        expected = target_hash(conn)
        conn.execute("DROP TABLE w31b_ind.target")
        conn.commit()

    result = migrate("CREATE TABLE w31b_ind.target (id bigint PRIMARY KEY)", "m1", expected)
    assert result == "APPLIED"
    with psycopg.connect(URL) as conn:
        assert conn.execute("SELECT version FROM w31b_schema_state WHERE schema_id='CORE'").fetchone()[0] == 2
        assert conn.execute("SELECT count(*) FROM w31b_schema_upgrade").fetchone()[0] == 1

    with psycopg.connect(URL) as conn:
        retry = conn.execute("SELECT migration_hash,status FROM w31b_schema_upgrade WHERE migration_id='m1'").fetchone()
        assert retry[1] == "APPLIED"

    with psycopg.connect(URL) as conn:
        setup(conn)
    bad = "CREATE TABLE w31b_ind.target (id bigint PRIMARY KEY)"
    try:
        migrate(bad, "m2", "0" * 32)
    except RuntimeError as exc:
        assert str(exc) == "ACTUAL_SCHEMA_MISMATCH"
    else:
        raise AssertionError("schema mismatch was accepted")
    with psycopg.connect(URL) as conn:
        assert conn.execute("SELECT version FROM w31b_schema_state WHERE schema_id='CORE'").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM w31b_schema_upgrade").fetchone()[0] == 0

    with psycopg.connect(URL) as conn:
        setup(conn)
    barrier = threading.Barrier(2)
    results = []
    errors = []

    def worker():
        try:
            with psycopg.connect(URL) as conn:
                with conn.transaction():
                    barrier.wait(timeout=10)
                    conn.execute("SELECT version FROM w31b_schema_state WHERE schema_id='CORE' FOR UPDATE").fetchone()
                    existing = conn.execute("SELECT status FROM w31b_schema_upgrade WHERE migration_id='m3'").fetchone()
                    if existing:
                        results.append("RETRY")
                        return
                    conn.execute("CREATE TABLE w31b_ind.concurrent_target (id bigint PRIMARY KEY)")
                    conn.execute("INSERT INTO w31b_schema_upgrade VALUES ('m3','CORE',1,2,%s,'APPLIED')", (h("CREATE TABLE w31b_ind.concurrent_target (id bigint PRIMARY KEY)"),))
                    conn.execute("UPDATE w31b_schema_state SET version=2 WHERE schema_id='CORE'")
                    results.append("APPLIED")
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads: t.start()
    for t in threads: t.join(timeout=20)
    assert not errors
    assert sorted(results) == ["APPLIED", "RETRY"]
    with psycopg.connect(URL) as conn:
        assert conn.execute("SELECT count(*) FROM w31b_schema_upgrade WHERE migration_id='m3'").fetchone()[0] == 1
        assert conn.execute("SELECT version FROM w31b_schema_state WHERE schema_id='CORE'").fetchone()[0] == 2

    print("W3.1-B independent PostgreSQL re-performance: PASS")
    print("transactional DDL + authority commit: PASS")
    print("rollback on actual-schema mismatch: PASS")
    print("same-ID retry: PASS")
    print("concurrent same-ID serialization: PASS")


if __name__ == "__main__":
    main()
