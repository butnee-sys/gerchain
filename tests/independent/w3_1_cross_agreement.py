"""W3.1 cross-agreement on one live PostgreSQL schema.

The production code is never imported. The existing independent PostgreSQL
observer and a separately written catalog traversal both derive a logical
schema from the same database; their descriptors and fingerprints must agree.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import uuid
from pathlib import Path

import psycopg

DB_URL = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
if not DB_URL:
    raise SystemExit("GERCHAIN_TEST_DATABASE_URL is required")
DB_URL = DB_URL.replace("postgresql+psycopg://", "postgresql://", 1)

_OBSERVER_PATH = Path(__file__).with_name("w3_1_postgres_schema_reperformance.py")
_SPEC = importlib.util.spec_from_file_location("w31_pg_observer", _OBSERVER_PATH)
assert _SPEC and _SPEC.loader
_OBSERVER = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _OBSERVER
_SPEC.loader.exec_module(_OBSERVER)


def second_descriptor(conn: psycopg.Connection, schema: str) -> dict:
    """Separate catalog implementation using independent query structure."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT n.nspname,c.oid,c.relname,a.attnum,a.attname,
                   format_type(a.atttypid,a.atttypmod),a.atttypmod,
                   NOT a.attnotnull,pg_get_expr(d.adbin,d.adrelid)
            FROM pg_attribute a
            JOIN pg_class c ON c.oid=a.attrelid
            JOIN pg_namespace n ON n.oid=c.relnamespace
            LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
            WHERE n.nspname=%s AND c.relkind='r' AND a.attnum>0 AND NOT a.attisdropped
            ORDER BY c.relname,a.attnum
        """, (schema,))
        tables={}; relids={}
        for ns,oid,table,attnum,name,typ,typmod,nullable,default in cur.fetchall():
            relids[(ns,table)]=int(oid)
            tables.setdefault((ns,table),{"namespace":ns,"name":table,"columns":[],
                "primary_keys":[],"unique_constraints":[],"checks":[],"foreign_keys":[]})
            tables[(ns,table)]["columns"].append({"ordinal":int(attnum),"name":name,
                "type":{"display":typ,"typmod":int(typmod)},"nullable":bool(nullable),
                "default":None if default is None else default.strip()})

        def attnames(relid, nums):
            if not nums:return []
            cur.execute("""
                SELECT a.attnum,a.attname FROM pg_attribute a
                WHERE a.attrelid=%s AND a.attnum=ANY(%s::smallint[])
                ORDER BY array_position(%s::smallint[],a.attnum)
            """,(relid,list(nums),list(nums)))
            return [r[1] for r in cur.fetchall()]

        cur.execute("""
            SELECT con.conrelid,con.contype,con.conname,con.conkey,
                   con.confrelid,con.confkey,con.confupdtype,con.confdeltype,
                   pg_get_constraintdef(con.oid,true),rn.nspname,rr.relname
            FROM pg_constraint con
            JOIN pg_class r ON r.oid=con.conrelid
            JOIN pg_namespace rn ON rn.oid=r.relnamespace
            LEFT JOIN pg_class rr ON rr.oid=con.confrelid
            WHERE rn.nspname=%s AND con.contype IN ('p','u','c','f')
            ORDER BY con.conname
        """,(schema,))
        for relid,kind,name,conkey,confrelid,confkey,up,down,definition,refns,reftable in cur.fetchall():
            table=next(k for k,v in relids.items() if v==int(relid)); item=tables[table]
            cols=attnames(int(relid),conkey)
            if kind=='p': item['primary_keys'].append({'name':name,'columns':cols})
            elif kind=='u': item['unique_constraints'].append({'name':name,'columns':cols})
            elif kind=='c': item['checks'].append({'name':name,'expression':definition.strip()})
            else: item['foreign_keys'].append({'name':name,'columns':cols,
                'referenced_table':[refns,reftable],
                'referenced_columns':attnames(int(confrelid),confkey),
                'on_update':up,'on_delete':down})

        cur.execute("""
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
            ORDER BY i.relname
        """,(schema,))
        indexes=[]
        for ns,table,name,unique,method,indkey,nkeys,natts in cur.fetchall():
            keys=[int(x) for x in indkey]
            if 0 in keys: continue
            relid=relids[(ns,table)]
            indexes.append({'namespace':ns,'name':name,'table':[ns,table],
                'unique':bool(unique),'method':method.lower(),
                'key_columns':attnames(relid,keys[:int(nkeys)]),
                'included_columns':attnames(relid,keys[int(nkeys):int(natts)])})

    for t in tables.values():
        t['columns'].sort(key=lambda x:(x['ordinal'],x['name']))
        for key in ('primary_keys','unique_constraints','checks','foreign_keys'):
            t[key].sort(key=lambda x:x['name'])
    return {'tables':[tables[k] for k in sorted(tables)],
            'indexes':sorted(indexes,key=lambda x:(x['namespace'],x['name']))}


def build_fixture(conn: psycopg.Connection, schema: str) -> None:
    conn.execute(f'CREATE SCHEMA "{schema}"')
    conn.execute(f'''CREATE TABLE "{schema}".owners (
        id bigint PRIMARY KEY,name text NOT NULL UNIQUE)''')
    conn.execute(f'''CREATE TABLE "{schema}".accounts (
        id bigint PRIMARY KEY,owner_id bigint NOT NULL,
        balance bigint NOT NULL DEFAULT 0,code text,
        CONSTRAINT accounts_balance_ck CHECK (balance >= 0),
        CONSTRAINT accounts_owner_fk FOREIGN KEY(owner_id)
          REFERENCES "{schema}".owners(id) ON UPDATE CASCADE ON DELETE RESTRICT)''')
    conn.execute(f'CREATE UNIQUE INDEX accounts_code_idx ON "{schema}".accounts(code)')


def main() -> None:
    schema='w31_cross_'+uuid.uuid4().hex[:12]
    with psycopg.connect(DB_URL,autocommit=True) as conn:
        try:
            build_fixture(conn,schema)
            observed=_OBSERVER.descriptor(conn,schema)
            independent=second_descriptor(conn,schema)
            assert observed == independent, (observed, independent)
            observed_fp=_OBSERVER.sha(observed)
            independent_fp=_OBSERVER.sha(independent)
            assert observed_fp == independent_fp
            print('W3.1 cross-agreement: PASS')
            print('descriptor_equal=True')
            print('fingerprint_equal=True')
            print('fingerprint='+observed_fp)
        finally:
            conn.execute(f'DROP SCHEMA "{schema}" CASCADE')


if __name__=='__main__':
    main()
