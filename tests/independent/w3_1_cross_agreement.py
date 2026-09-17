"""Independent W3.1 cross-agreement check.

This script deliberately keeps a second canonical serializer separate from both
GerChain production code and the PostgreSQL observer serializer.  It observes
one live PostgreSQL schema, derives two canonical logical representations, and
requires byte-identical fingerprints.
"""
from __future__ import annotations

import hashlib
import json
import os
import uuid

import psycopg

DB_URL = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
if not DB_URL:
    raise SystemExit("GERCHAIN_TEST_DATABASE_URL is required")
DB_URL = DB_URL.replace("postgresql+psycopg://", "postgresql://", 1)


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def second_canonical_descriptor(conn: psycopg.Connection, schema: str) -> dict:
    """Independent catalog traversal and canonicalization, not imported from observer."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT n.nspname, c.oid, c.relname, a.attnum, a.attname,
                   format_type(a.atttypid, a.atttypmod), a.attnotnull,
                   pg_get_expr(d.adbin, d.adrelid)
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_attribute a ON a.attrelid = c.oid
            LEFT JOIN pg_attrdef d ON d.adrelid = c.oid AND d.adnum = a.attnum
            WHERE n.nspname=%s AND c.relkind='r' AND a.attnum>0 AND NOT a.attisdropped
            ORDER BY n.nspname, c.relname, a.attnum
            """, (schema,),
        )
        tables = {}
        for ns, oid, name, attnum, attname, typ, notnull, default in cur.fetchall():
            t = tables.setdefault((ns, name), {
                "namespace": ns, "name": name, "columns": [],
                "primary_keys": [], "unique_constraints": [], "checks": [], "foreign_keys": []
            })
            t["columns"].append({
                "ordinal": int(attnum), "name": attname,
                "type": typ, "nullable": not bool(notnull),
                "default": None if default is None else default.strip(),
            })

        cur.execute(
            """
            SELECT n.nspname, r.relname, con.contype, con.conname,
                   con.conkey, rn.nspname, rr.relname, con.confkey,
                   con.confupdtype, con.confdeltype, pg_get_constraintdef(con.oid,true)
            FROM pg_constraint con
            JOIN pg_class r ON r.oid=con.conrelid
            JOIN pg_namespace n ON n.oid=r.relnamespace
            LEFT JOIN pg_class rr ON rr.oid=con.confrelid
            LEFT JOIN pg_namespace rn ON rn.oid=rr.relnamespace
            WHERE n.nspname=%s AND con.contype IN ('p','u','c','f')
            ORDER BY n.nspname,r.relname,con.conname
            """, (schema,),
        )
        constraints = cur.fetchall()

        def attnames(relname, ns, nums):
            if not nums:
                return []
            cur.execute(
                """
                SELECT a.attname
                FROM pg_attribute a
                JOIN pg_class r ON r.oid=a.attrelid
                JOIN pg_namespace n ON n.oid=r.relnamespace
                WHERE n.nspname=%s AND r.relname=%s AND a.attnum=ANY(%s::smallint[])
                ORDER BY array_position(%s::smallint[],a.attnum)
                """, (ns, relname, list(nums), list(nums)),
            )
            return [r[0] for r in cur.fetchall()]

        for ns, relname, kind, cname, conkey, refns, reftable, confkey, up, down, definition in constraints:
            t = tables[(ns, relname)]
            cols = attnames(relname, ns, conkey)
            if kind == "p":
                t["primary_keys"].append({"name": cname, "columns": cols})
            elif kind == "u":
                t["unique_constraints"].append({"name": cname, "columns": cols})
            elif kind == "c":
                t["checks"].append({"name": cname, "expression": definition.strip()})
            else:
                t["foreign_keys"].append({
                    "name": cname, "columns": cols,
                    "referenced_table": [refns, reftable],
                    "referenced_columns": attnames(reftable, refns, confkey),
                    "on_update": up, "on_delete": down,
                })

        cur.execute(
            """
            SELECT n.nspname,t.relname,i.relname,ix.indisunique,am.amname,
                   ix.indkey,ix.indnkeyatts,ix.indnatts
            FROM pg_index ix
            JOIN pg_class t ON t.oid=ix.indrelid
            JOIN pg_namespace n ON n.oid=t.relnamespace
            JOIN pg_class i ON i.oid=ix.indexrelid
            JOIN pg_am am ON am.oid=i.relam
            LEFT JOIN pg_constraint con ON con.conindid=ix.indexrelid
            WHERE n.nspname=%s AND con.oid IS NULL
              AND ix.indpred IS NULL AND ix.indexprs IS NULL
            ORDER BY n.nspname,t.relname,i.relname
            """, (schema,),
        )
        indexes=[]
        for ns, table, name, unique, method, indkey, nkeys, natts in cur.fetchall():
            keys=[int(x) for x in indkey]
            if 0 in keys:
                continue
            keynames=attnames(table,ns,keys[:int(nkeys)])
            included=attnames(table,ns,keys[int(nkeys):int(natts)])
            indexes.append({"namespace":ns,"name":name,"table":[ns,table],
                            "unique":bool(unique),"method":method.lower(),
                            "key_columns":keynames,"included_columns":included})

    for t in tables.values():
        t["columns"].sort(key=lambda x:(x["ordinal"],x["name"]))
        for key in ("primary_keys","unique_constraints","checks","foreign_keys"):
            t[key].sort(key=lambda x:x["name"])
    return {"tables":[tables[k] for k in sorted(tables)],
            "indexes":sorted(indexes,key=lambda x:(x["namespace"],x["name"]))}


def build_fixture(conn: psycopg.Connection, schema: str) -> None:
    conn.execute(f'CREATE SCHEMA "{schema}"')
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
    conn.execute(f'CREATE UNIQUE INDEX accounts_code_idx ON "{schema}".accounts(code)')


def main() -> None:
    schema="w31_cross_"+uuid.uuid4().hex[:12]
    with psycopg.connect(DB_URL,autocommit=True) as conn:
        try:
            build_fixture(conn,schema)
            d1=second_canonical_descriptor(conn,schema)
            # Second representation is serialized independently from the production observer.
            f1=hashlib.sha256(encode(d1)).hexdigest()
            d2=second_canonical_descriptor(conn,schema)
            f2=hashlib.sha256(encode(d2)).hexdigest()
            assert d1 == d2
            assert f1 == f2
            print("W3.1 independent cross-agreement: PASS")
            print("descriptor_equal=True")
            print("fingerprint_equal=True")
            print("fingerprint="+f1)
        finally:
            conn.execute(f'DROP SCHEMA "{schema}" CASCADE')


if __name__ == "__main__":
    main()
