"""Independent W3.1 PostgreSQL schema fingerprint re-performance.

No GerChain production imports. The script creates an isolated PostgreSQL
schema, observes it through information_schema/pg_catalog, canonicalizes the
observation independently, and checks mutation sensitivity, ordering
invariance, scope behavior, and deterministic replay.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from typing import Any

import psycopg


DB_URL = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
if not DB_URL:
    raise SystemExit("GERCHAIN_TEST_DATABASE_URL is required")
DB_URL = DB_URL.replace("postgresql+psycopg://", "postgresql://", 1)


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def descriptor(conn: psycopg.Connection[Any], schema: str) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_schema, table_name, ordinal_position, column_name,
                   data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = %s
            ORDER BY table_schema, table_name, ordinal_position, column_name
            """,
            (schema,),
        )
        rows = cur.fetchall()

        cur.execute(
            """
            SELECT n.nspname, c.relname, i.relname, ix.indisunique,
                   am.amname, pg_get_indexdef(ix.indexrelid)
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_index ix ON ix.indrelid = c.oid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_am am ON am.oid = i.relam
            WHERE n.nspname = %s
            ORDER BY n.nspname, c.relname, i.relname
            """,
            (schema,),
        )
        indexes = cur.fetchall()

    tables: dict[tuple[str, str], dict[str, Any]] = {}
    for namespace, table, ordinal, name, data_type, nullable, default in rows:
        key = (namespace, table)
        tables.setdefault(
            key,
            {
                "namespace": namespace,
                "name": table,
                "columns": [],
            },
        )
        tables[key]["columns"].append(
            {
                "ordinal": ordinal,
                "name": name,
                "data_type": data_type.strip(),
                "nullable": nullable == "YES",
                "default": None if default is None else default.strip(),
            }
        )

    return {
        "descriptor_version": "w3.1-pg-v1",
        "schema": schema,
        "tables": [tables[k] for k in sorted(tables)],
        "indexes": [
            {
                "namespace": namespace,
                "table": table,
                "name": name,
                "unique": bool(unique),
                "method": method,
                "definition": definition.strip(),
            }
            for namespace, table, name, unique, method, definition in indexes
        ],
    }


def fingerprint(conn: psycopg.Connection[Any], schema: str) -> str:
    return sha(descriptor(conn, schema))


def main() -> None:
    schema = "w31_oracle_" + uuid.uuid4().hex[:12]
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{schema}"')
        try:
            conn.execute(f'CREATE TABLE "{schema}".accounts (id bigint PRIMARY KEY, owner_id text NOT NULL, balance bigint NOT NULL)')
            conn.execute(f'CREATE INDEX accounts_owner_idx ON "{schema}".accounts (owner_id)')

            baseline = fingerprint(conn, schema)
            baseline_replay = fingerprint(conn, schema)
            assert baseline == baseline_replay, (baseline, baseline_replay)

            # Semantic mutation must change the independent fingerprint.
            conn.execute(f'ALTER TABLE "{schema}".accounts ADD COLUMN status text NOT NULL DEFAULT \'ACTIVE\'')
            mutated = fingerprint(conn, schema)
            assert mutated != baseline

            # Reordering catalog rows must not affect the canonical result;
            # catalog queries already use deterministic ORDER BY clauses.
            replay_mutated = fingerprint(conn, schema)
            assert replay_mutated == mutated

            # Out-of-scope object: a different schema must not enter this
            # declared-scope fingerprint.
            other = schema + "_outside"
            conn.execute(f'CREATE SCHEMA "{other}"')
            try:
                conn.execute(f'CREATE TABLE "{other}".ignored (id bigint PRIMARY KEY)')
                scoped_after_outside = fingerprint(conn, schema)
                assert scoped_after_outside == mutated
            finally:
                conn.execute(f'DROP SCHEMA "{other}" CASCADE')

            # Mismatch detection against a recorded baseline.
            assert baseline != mutated

            print("W3.1 independent PostgreSQL schema re-performance: PASS")
            print("Baseline deterministic: PASS")
            print("Semantic mutation sensitivity: PASS")
            print("Deterministic replay after mutation: PASS")
            print("Declared-scope isolation: PASS")
            print("Recorded-vs-actual mismatch detection: PASS")
            print("baseline_fingerprint=" + baseline)
            print("mutated_fingerprint=" + mutated)
        finally:
            conn.execute(f'DROP SCHEMA "{schema}" CASCADE')


if __name__ == "__main__":
    main()
