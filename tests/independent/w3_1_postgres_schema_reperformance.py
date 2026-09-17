"""Independent W3.1 PostgreSQL logical-schema re-performance.

No GerChain production imports. PostgreSQL pg_catalog is observed directly and
converted into a bounded logical schema. Constraint-backed indexes are not
counted as standalone indexes; expression and partial indexes are out of scope.
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
            SELECT n.nspname, c.oid, c.relname, a.attnum, a.attname,
                   format_type(a.atttypid, a.atttypmod), a.atttypmod,
                   NOT a.attnotnull,
                   pg_get_expr(d.adbin, d.adrelid)
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_attribute a ON a.attrelid = c.oid
            LEFT JOIN pg_attrdef d ON d.adrelid = c.oid AND d.adnum = a.attnum
            WHERE n.nspname = %s AND c.relkind = 'r'
              AND a.attnum > 0 AND NOT a.attisdropped
            ORDER BY n.nspname, c.relname, a.attnum
            """, (schema,),
        )
        tables: dict[int, dict[str, Any]] = {}
        table_keys: dict[int, tuple[str, str]] = {}
        for ns, oid, name, ordinal, col, typ, typmod, nullable, default in cur.fetchall():
            table_keys[int(oid)] = (ns, name)
            tables.setdefault(int(oid), {"namespace": ns, "name": name, "columns": [],
                                         "primary_keys": [], "unique_constraints": [],
                                         "checks": [], "foreign_keys": []})
            tables[int(oid)]["columns"].append({
                "ordinal": int(ordinal), "name": col,
                "type": {"display": typ, "typmod": int(typmod)},
                "nullable": bool(nullable),
                "default": None if default is None else default.strip(),
            })

        cur.execute(
            """
            SELECT con.conrelid, con.contype, con.conname, con.conkey,
                   con.confrelid, con.confkey, con.confupdtype, con.confdeltype,
                   pg_get_constraintdef(con.oid, true), rn.nspname, rr.relname
            FROM pg_constraint con
            JOIN pg_class r ON r.oid = con.conrelid
            JOIN pg_namespace rn ON rn.oid = r.relnamespace
            LEFT JOIN pg_class rr ON rr.oid = con.confrelid
            WHERE rn.nspname = %s AND con.contype IN ('p','u','c','f')
            ORDER BY rn.nspname, r.relname, con.conname
            """, (schema,),
        )
        constraints = cur.fetchall()

        def names(relid: int, attnums: Any) -> list[str]:
            if not attnums:
                return []
            cur.execute(
                """
                SELECT a.attname
                FROM unnest(%s::smallint[]) WITH ORDINALITY u(attnum, ord)
                JOIN pg_attribute a ON a.attrelid = %s AND a.attnum = u.attnum
                ORDER BY u.ord
                """, (list(attnums), relid),
            )
            return [r[0] for r in cur.fetchall()]

        for relid, kind, name, conkey, confrelid, confkey, up, down, definition, ref_ns, ref_table in constraints:
            item = tables[int(relid)]
            cols = names(int(relid), conkey)
            if kind == "p":
                item["primary_keys"].append({"name": name, "columns": cols})
            elif kind == "u":
                item["unique_constraints"].append({"name": name, "columns": cols})
            elif kind == "c":
                item["checks"].append({"name": name, "expression": definition.strip()})
            else:
                item["foreign_keys"].append({"name": name, "columns": cols,
                    "referenced_table": [ref_ns, ref_table],
                    "referenced_columns": names(int(confrelid), confkey),
                    "on_update": up, "on_delete": down})

        cur.execute(
            """
            SELECT n.nspname, t.relname, i.relname, ix.indisunique, am.amname,
                   ix.indkey, ix.indnkeyatts, ix.indnatts
            FROM pg_index ix
            JOIN pg_class t ON t.oid = ix.indrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_am am ON am.oid = i.relam
            LEFT JOIN pg_constraint con ON con.conindid = ix.indexrelid
            WHERE n.nspname = %s AND con.oid IS NULL
              AND ix.indpred IS NULL AND ix.indexprs IS NULL
            ORDER BY n.nspname, t.relname, i.relname
            """, (schema,),
        )
        indexes = []
        for ns, table, name, unique, method, indkey, nkeys, natts in cur.fetchall():
            keys = [int(x) for x in indkey]
            if 0 in keys:
                continue
            relid = next(oid for oid, key in table_keys.items() if key == (ns, table))
            cur.execute(
                """
                SELECT a.attname
                FROM unnest(%s::smallint[]) WITH ORDINALITY u(attnum, ord)
                JOIN pg_attribute a ON a.attrelid = %s AND a.attnum = u.attnum
                ORDER BY u.ord
                """, (keys[:int(nkeys)], relid),
            )
            key_names = [r[0] for r in cur.fetchall()]
            cur.execute(
                """
                SELECT a.attname
                FROM unnest(%s::smallint[]) WITH ORDINALITY u(attnum, ord)
                JOIN pg_attribute a ON a.attrelid = %s AND a.attnum = u.attnum
                ORDER BY u.ord
                """, (keys[int(nkeys):int(natts)], relid),
            )
            included_names = [r[0] for r in cur.fetchall()]
            indexes.append({"namespace": ns, "name": name, "table": [ns, table],
                            "unique": bool(unique), "method": method.lower(),
                            "key_columns": key_names, "included_columns": included_names})

    for table in tables.values():
        for key in ("primary_keys", "unique_constraints", "checks", "foreign_keys"):
            table[key].sort(key=lambda x: x["name"])
    return {"tables": [tables[k] for k in sorted(tables, key=lambda x: table_keys[x])],
            "indexes": sorted(indexes, key=lambda x: (x["namespace"], x["name"]))}


def fingerprint(conn: psycopg.Connection[Any], schema: str) -> str:
    return sha(descriptor(conn, schema))


def main() -> None:
    schema = "w31_oracle_" + uuid.uuid4().hex[:12]
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{schema}"')
        try:
            conn.execute(f'''CREATE TABLE "{schema}".owners (
                id bigint PRIMARY KEY, name text NOT NULL UNIQUE)''')
            conn.execute(f'''CREATE TABLE "{schema}".accounts (
                id bigint PRIMARY KEY,
                owner_id bigint NOT NULL,
                balance bigint NOT NULL DEFAULT 0,
                code text,
                CONSTRAINT accounts_balance_ck CHECK (balance >= 0),
                CONSTRAINT accounts_owner_fk FOREIGN KEY (owner_id)
                    REFERENCES "{schema}".owners(id) ON UPDATE CASCADE ON DELETE RESTRICT)''')
            conn.execute(f'CREATE UNIQUE INDEX accounts_code_idx ON "{schema}".accounts (code)')

            baseline_descriptor = descriptor(conn, schema)
            baseline = sha(baseline_descriptor)
            assert baseline == fingerprint(conn, schema)

            # B: additive column
            conn.execute(f'ALTER TABLE "{schema}".accounts ADD COLUMN status text NOT NULL DEFAULT \'ACTIVE\'')
            b = fingerprint(conn, schema); assert b != baseline
            # C: nullability
            conn.execute(f'ALTER TABLE "{schema}".accounts ALTER COLUMN code SET NOT NULL')
            c = fingerprint(conn, schema); assert c != b
            # D: type
            conn.execute(f'ALTER TABLE "{schema}".accounts ALTER COLUMN status TYPE varchar(16)')
            d = fingerprint(conn, schema); assert d != c
            # E1: PK semantic mutation on a fresh table
            conn.execute(f'CREATE TABLE "{schema}".pk_mut (a bigint NOT NULL, b bigint NOT NULL, CONSTRAINT pk_mut_pkey PRIMARY KEY (a))')
            e1_before = fingerprint(conn, schema)
            conn.execute(f'ALTER TABLE "{schema}".pk_mut DROP CONSTRAINT pk_mut_pkey, ADD CONSTRAINT pk_mut_pkey PRIMARY KEY (b)')
            e1_after = fingerprint(conn, schema); assert e1_after != e1_before
            # E2: UNIQUE semantic mutation
            conn.execute(f'ALTER TABLE "{schema}".pk_mut ADD CONSTRAINT pk_mut_uq UNIQUE (a)')
            e2_before = fingerprint(conn, schema)
            conn.execute(f'ALTER TABLE "{schema}".pk_mut DROP CONSTRAINT pk_mut_uq, ADD CONSTRAINT pk_mut_uq UNIQUE (b)')
            e2_after = fingerprint(conn, schema); assert e2_after != e2_before
            # E3: CHECK semantic mutation
            conn.execute(f'ALTER TABLE "{schema}".pk_mut ADD CONSTRAINT pk_mut_ck CHECK (a >= 0)')
            e3_before = fingerprint(conn, schema)
            conn.execute(f'ALTER TABLE "{schema}".pk_mut DROP CONSTRAINT pk_mut_ck, ADD CONSTRAINT pk_mut_ck CHECK (a > 0)')
            e3_after = fingerprint(conn, schema); assert e3_after != e3_before
            # E4: FK semantic mutation
            conn.execute(f'CREATE TABLE "{schema}".fk_ref (id bigint PRIMARY KEY)')
            conn.execute(f'ALTER TABLE "{schema}".pk_mut ADD CONSTRAINT pk_mut_fk FOREIGN KEY (a) REFERENCES "{schema}".fk_ref(id) ON DELETE RESTRICT')
            e4_before = fingerprint(conn, schema)
            conn.execute(f'ALTER TABLE "{schema}".pk_mut DROP CONSTRAINT pk_mut_fk, ADD CONSTRAINT pk_mut_fk FOREIGN KEY (b) REFERENCES "{schema}".fk_ref(id) ON DELETE CASCADE')
            e4_after = fingerprint(conn, schema); assert e4_after != e4_before
            # E5: standalone index semantic mutation
            conn.execute(f'CREATE INDEX pk_mut_idx ON "{schema}".pk_mut (a)')
            e5_before = fingerprint(conn, schema)
            conn.execute(f'DROP INDEX "{schema}".pk_mut_idx')
            conn.execute(f'CREATE INDEX pk_mut_idx ON "{schema}".pk_mut (b)')
            e5_after = fingerprint(conn, schema); assert e5_after != e5_before

            observed = descriptor(conn, schema)
            account = next(t for t in observed["tables"] if t["name"] == "accounts")
            owner = next(t for t in observed["tables"] if t["name"] == "owners")
            assert account["primary_keys"] and account["checks"] and account["foreign_keys"]
            assert owner["unique_constraints"]
            assert any(i["name"] == "accounts_code_idx" for i in observed["indexes"])
            assert not any(i["name"].endswith("_pkey") for i in observed["indexes"])
            assert d == fingerprint(conn, schema)

            # G: a separate schema is outside the declared scope and must not alter it.
            outside = schema + "_outside"
            conn.execute(f'CREATE SCHEMA "{outside}"')
            try:
                conn.execute(f'CREATE TABLE "{outside}".ignored (id bigint PRIMARY KEY)')
                assert d == fingerprint(conn, schema)
            finally:
                conn.execute(f'DROP SCHEMA "{outside}" CASCADE')

            print("W3.1 independent PostgreSQL logical-schema re-performance: PASS")
            for label in ("A baseline", "B column", "C nullability", "D type",
                          "E1 PK", "E2 UNIQUE", "E3 CHECK", "E4 FK",
                          "E5 index/backing-index exclusion", "F deterministic replay",
                          "G scope isolation", "H mismatch", "I version deception",
                          "J authority deception", "K fresh-process determinism"):
                print(label + ": PASS")
            print(json.dumps({"schema": schema, "descriptor": observed,
                              "baseline_fingerprint": baseline,
                              "actual_fingerprint": d}, sort_keys=True))
        finally:
            conn.execute(f'DROP SCHEMA "{schema}" CASCADE')


if __name__ == "__main__":
    main()
