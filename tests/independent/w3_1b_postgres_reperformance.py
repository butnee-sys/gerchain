"""Independent PostgreSQL re-performance of the W3.1-B contract.

This implementation intentionally does not import GerChain production
migration, schema-authority, reconciliation, or fingerprint code. It observes
PostgreSQL directly and independently implements the W3.1-A v1.1 logical
schema domain used by W3.1-B: tables, columns/types/nullability/defaults,
PK/UNIQUE/CHECK/FK constraints, and ordinary standalone indexes.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading

import psycopg


URL = os.environ["GERCHAIN_TEST_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
SCHEMA = "w31b_ind"
DESCRIPTOR_VERSION = "w3.1-v1.1"


def _norm(value: str | None) -> str | None:
    if value is None:
        return None
    return " ".join(value.strip().split())


def _type(row) -> dict:
    params = []
    if row["typmod"] is not None and row["typmod"] >= 0:
        params.append(["typmod", int(row["typmod"])])
    return {
        "schema": row["type_schema"],
        "name": row["type_name"],
        "parameters": params,
        "array_dimensions": int(row["array_dimensions"] or 0),
    }


def descriptor(conn):
    tables = []
    table_rows = conn.execute(
        """SELECT n.nspname AS namespace, c.relname AS name
           FROM pg_catalog.pg_class c
           JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
           WHERE n.nspname = %s AND c.relkind = 'r'
           ORDER BY c.relname""",
        (SCHEMA,),
    ).fetchall()

    for table_row in table_rows:
        namespace, table_name = table_row
        qualified = f'"{namespace}"."{table_name}"'
        column_rows = conn.execute(
            """SELECT a.attnum AS ordinal, a.attname AS name,
                      a.attnotnull AS nullable_not, a.atttypmod AS typmod,
                      t.typname AS type_name, tn.nspname AS type_schema,
                      CASE WHEN t.typelem <> 0 AND t.typtype = 'b' THEN 1 ELSE 0 END AS array_dimensions,
                      pg_get_expr(ad.adbin, ad.adrelid) AS default_expression
               FROM pg_catalog.pg_attribute a
               JOIN pg_catalog.pg_type t ON t.oid = a.atttypid
               JOIN pg_catalog.pg_namespace tn ON tn.oid = t.typnamespace
               LEFT JOIN pg_catalog.pg_attrdef ad ON ad.adrelid=a.attrelid AND ad.adnum=a.attnum
               WHERE a.attrelid = to_regclass(%s)::oid AND a.attnum > 0 AND NOT a.attisdropped
               ORDER BY a.attnum""",
            (qualified,),
        ).fetchall()
        columns = {
            int(r["ordinal"]): {
                "ordinal": int(r["ordinal"]),
                "name": r["name"],
                "type": _type(r),
                "nullable": not bool(r["nullable_not"]),
                "default": _norm(r["default_expression"]),
            }
            for r in column_rows
        }

        constraints = {"primary_keys": [], "unique_constraints": [], "foreign_keys": [], "checks": []}
        constraint_rows = conn.execute(
            """SELECT con.conname, con.contype, con.conkey::int[] AS local_keys,
                      con.confkey::int[] AS foreign_keys,
                      fn.nspname AS foreign_schema, fc.relname AS foreign_table,
                      con.confupdtype, con.confdeltype,
                      pg_get_constraintdef(con.oid, true) AS definition
               FROM pg_catalog.pg_constraint con
               JOIN pg_catalog.pg_class c ON c.oid=con.conrelid
               JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
               LEFT JOIN pg_catalog.pg_class fc ON fc.oid=con.confrelid
               LEFT JOIN pg_catalog.pg_namespace fn ON fn.oid=fc.relnamespace
               WHERE n.nspname=%s AND c.relname=%s AND con.contype IN ('p','u','c','f')
               ORDER BY con.conname""",
            (namespace, table_name),
        ).fetchall()
        for row in constraint_rows:
            local = [columns[int(v)]["name"] for v in (row["local_keys"] or [])]
            if row["contype"] == "p":
                constraints["primary_keys"].append({"name": row["conname"], "columns": local})
            elif row["contype"] == "u":
                constraints["unique_constraints"].append({"name": row["conname"], "columns": local})
            elif row["contype"] == "c":
                constraints["checks"].append({"name": row["conname"], "expression": _norm(row["definition"])})
            else:
                ref = conn.execute(
                    """SELECT a.attname, x.position
                       FROM unnest(%s::int[]) WITH ORDINALITY AS x(attnum, position)
                       JOIN pg_catalog.pg_attribute a ON a.attrelid=to_regclass(%s)::oid AND a.attnum=x.attnum
                       ORDER BY x.position""",
                    (list(row["foreign_keys"] or []), f'"{row["foreign_schema"]}"."{row["foreign_table"]}"'),
                ).fetchall()
                constraints["foreign_keys"].append({
                    "name": row["conname"],
                    "columns": local,
                    "referenced_table": [row["foreign_schema"], row["foreign_table"]],
                    "referenced_columns": [r["attname"] for r in ref],
                    "on_update": row["confupdtype"],
                    "on_delete": row["confdeltype"],
                })

        tables.append({
            "namespace": namespace,
            "name": table_name,
            "columns": sorted(columns.values(), key=lambda x: (x["ordinal"], x["name"])),
            "primary_keys": sorted(constraints["primary_keys"], key=lambda x: x["name"]),
            "unique_constraints": sorted(constraints["unique_constraints"], key=lambda x: x["name"]),
            "foreign_keys": sorted(constraints["foreign_keys"], key=lambda x: x["name"]),
            "checks": sorted(constraints["checks"], key=lambda x: x["name"]),
        })

    indexes = []
    index_rows = conn.execute(
        """SELECT n.nspname AS namespace, i.relname AS index_name,
                  tn.nspname AS table_namespace, t.relname AS table_name,
                  ix.indisunique AS unique_index, am.amname AS method,
                  ix.indkey::int[] AS key_attnums, ix.indnkeyatts,
                  ix.indpred IS NOT NULL AS partial, ix.indexprs IS NOT NULL AS expression,
                  EXISTS (SELECT 1 FROM pg_catalog.pg_constraint c
                          WHERE c.conindid=ix.indexrelid AND c.contype IN ('p','u')) AS backing_constraint
           FROM pg_catalog.pg_index ix
           JOIN pg_catalog.pg_class i ON i.oid=ix.indexrelid
           JOIN pg_catalog.pg_class t ON t.oid=ix.indrelid
           JOIN pg_catalog.pg_namespace n ON n.oid=i.relnamespace
           JOIN pg_catalog.pg_namespace tn ON tn.oid=t.relnamespace
           JOIN pg_catalog.pg_am am ON am.oid=i.relam
           WHERE tn.nspname=%s ORDER BY i.relname""",
        (SCHEMA,),
    ).fetchall()
    for row in index_rows:
        if row["partial"] or row["expression"] or row["backing_constraint"]:
            continue
        table = f'"{row["table_namespace"]}"."{row["table_name"]}"'
        attrs = conn.execute(
            """SELECT a.attname, x.position
               FROM unnest(%s::int[]) WITH ORDINALITY AS x(attnum, position)
               JOIN pg_catalog.pg_attribute a ON a.attrelid=to_regclass(%s)::oid AND a.attnum=x.attnum
               WHERE x.position <= %s ORDER BY x.position""",
            (list(row["key_attnums"] or []), table, int(row["indnkeyatts"])),
        ).fetchall()
        indexes.append({
            "namespace": row["namespace"],
            "name": row["index_name"],
            "table": [row["table_namespace"], row["table_name"]],
            "unique": bool(row["unique_index"]),
            "method": row["method"].strip().lower(),
            "key_columns": [r["attname"] for r in attrs],
            "included_columns": [],
        })

    return {"tables": sorted(tables, key=lambda x: (x["namespace"], x["name"])), "indexes": sorted(indexes, key=lambda x: (x["namespace"], x["name"]))}


def fingerprint(conn) -> str:
    payload = json.dumps(descriptor(conn), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def setup(conn):
    conn.execute(f'DROP SCHEMA IF EXISTS {SCHEMA} CASCADE')
    conn.execute(f'CREATE SCHEMA {SCHEMA}')
    conn.execute("DROP TABLE IF EXISTS w31b_schema_upgrade")
    conn.execute("DROP TABLE IF EXISTS w31b_schema_state")
    conn.execute("CREATE TABLE w31b_schema_state (schema_id text PRIMARY KEY, version integer NOT NULL, state_hash text NOT NULL)")
    conn.execute("CREATE TABLE w31b_schema_upgrade (migration_id text PRIMARY KEY, schema_id text NOT NULL, from_version integer NOT NULL, to_version integer NOT NULL, migration_hash text NOT NULL, status text NOT NULL)")
    conn.execute("INSERT INTO w31b_schema_state VALUES ('CORE', 1, %s)", (fingerprint(conn),))
    conn.commit()


def sql_hash(sql: str) -> str:
    return hashlib.sha256(_norm(sql).encode()).hexdigest()


def migrate(sql: str, migration_id: str, expected_hash: str, from_version: int = 1, to_version: int = 2):
    with psycopg.connect(URL) as conn:
        with conn.transaction():
            row = conn.execute("SELECT version,state_hash FROM w31b_schema_state WHERE schema_id='CORE' FOR UPDATE").fetchone()
            existing = conn.execute("SELECT migration_hash,status FROM w31b_schema_upgrade WHERE migration_id=%s", (migration_id,)).fetchone()
            if existing:
                if existing[1] == "APPLIED" and existing[0] == sql_hash(sql):
                    if fingerprint(conn) != expected_hash:
                        raise RuntimeError("ACTUAL_SCHEMA_MISMATCH")
                    return "RETRY"
                raise RuntimeError("IDENTITY_CONFLICT")
            if row[0] != from_version:
                raise RuntimeError("STALE_PREDECESSOR")
            if fingerprint(conn) != row[1]:
                raise RuntimeError("RECORDED_PREDECESSOR_MISMATCH")
            conn.execute(sql)
            actual = fingerprint(conn)
            if actual != expected_hash:
                raise RuntimeError("ACTUAL_SCHEMA_MISMATCH")
            conn.execute("INSERT INTO w31b_schema_upgrade VALUES (%s,'CORE',%s,%s,%s,'APPLIED')", (migration_id, from_version, to_version, sql_hash(sql)))
            conn.execute("UPDATE w31b_schema_state SET version=%s,state_hash=%s WHERE schema_id='CORE'", (to_version, actual))
            return "APPLIED"


def main():
    create_target = f"CREATE TABLE {SCHEMA}.target (id bigint PRIMARY KEY, value text NOT NULL)"
    with psycopg.connect(URL) as conn:
        setup(conn)
        conn.execute(create_target)
        expected = fingerprint(conn)
        conn.execute(f'DROP TABLE {SCHEMA}.target')
        conn.commit()

    assert migrate(create_target, "m1", expected) == "APPLIED"
    with psycopg.connect(URL) as conn:
        assert conn.execute("SELECT version FROM w31b_schema_state WHERE schema_id='CORE'").fetchone()[0] == 2
        assert conn.execute("SELECT count(*) FROM w31b_schema_upgrade").fetchone()[0] == 1
        assert fingerprint(conn) == expected

    with psycopg.connect(URL) as conn:
        setup(conn)
    bad_sql = f"CREATE TABLE {SCHEMA}.target (id bigint PRIMARY KEY)"
    try:
        migrate(bad_sql, "m2", "0" * 64)
    except RuntimeError as exc:
        assert str(exc) == "ACTUAL_SCHEMA_MISMATCH"
    else:
        raise AssertionError("schema mismatch was accepted")
    with psycopg.connect(URL) as conn:
        assert conn.execute("SELECT version FROM w31b_schema_state WHERE schema_id='CORE'").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM w31b_schema_upgrade").fetchone()[0] == 0
        assert conn.execute(f"SELECT to_regclass('{SCHEMA}.target')").fetchone()[0] is None

    with psycopg.connect(URL) as conn:
        setup(conn)
        conn.execute(f'CREATE TABLE {SCHEMA}.target (id bigint PRIMARY KEY)')
        conn.commit()
    with psycopg.connect(URL) as conn:
        external_hash = fingerprint(conn)
    try:
        migrate(bad_sql, "m3", external_hash)
    except RuntimeError as exc:
        assert str(exc) == "RECORDED_PREDECESSOR_MISMATCH"
    else:
        raise AssertionError("pre-applied physical DDL was silently adopted")

    with psycopg.connect(URL) as conn:
        setup(conn)
    concurrent_sql = f"CREATE TABLE {SCHEMA}.concurrent_target (id bigint PRIMARY KEY)"
    with psycopg.connect(URL) as conn:
        conn.execute(concurrent_sql)
        concurrent_expected = fingerprint(conn)
        conn.execute(f'DROP TABLE {SCHEMA}.concurrent_target')
        conn.commit()
    barrier = threading.Barrier(2)
    results = []
    errors = []

    def worker():
        try:
            barrier.wait(timeout=10)
            results.append(migrate(concurrent_sql, "m4", concurrent_expected))
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=20)
    assert not errors
    assert sorted(results) == ["APPLIED", "RETRY"]

    with psycopg.connect(URL) as conn:
        setup(conn)
        conn.execute(f'CREATE TABLE {SCHEMA}.semantic (id bigint PRIMARY KEY, value text NOT NULL)')
        baseline = fingerprint(conn)
        conn.execute(f'ALTER TABLE {SCHEMA}.semantic ADD COLUMN note text')
        changed = fingerprint(conn)
        assert changed != baseline
        conn.rollback()

    print(f"W3.1-B independent PostgreSQL re-performance ({DESCRIPTOR_VERSION}): PASS")
    print("transactional DDL + authority commit: PASS")
    print("rollback on actual-schema mismatch: PASS")
    print("recorded-predecessor recovery boundary: PASS")
    print("same-ID retry + concurrent serialization: PASS")
    print("semantic fingerprint sensitivity: PASS")


if __name__ == "__main__":
    main()
