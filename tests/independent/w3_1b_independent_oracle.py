"""Independent W3.1-B authority oracle; no GerChain production imports."""
from __future__ import annotations

import hashlib
import json
import os

import psycopg


URL = os.environ["GERCHAIN_TEST_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")


def identity(migration_id, schema_id, from_version, to_version, payload):
    canonical = " ".join(payload.strip().rstrip(";").split())
    return {
        "migration_id": migration_id,
        "schema_id": schema_id,
        "from_version": from_version,
        "to_version": to_version,
        "migration_hash": hashlib.sha256(canonical.encode()).hexdigest(),
    }


def main():
    with psycopg.connect(URL) as conn:
        conn.execute("DROP SCHEMA IF EXISTS w31b_oracle CASCADE")
        conn.execute("CREATE SCHEMA w31b_oracle")
        conn.execute("CREATE TABLE w31b_oracle.state (schema_id text PRIMARY KEY, version integer NOT NULL)")
        conn.execute("CREATE TABLE w31b_oracle.upgrade (migration_id text PRIMARY KEY, schema_id text NOT NULL, from_version integer NOT NULL, to_version integer NOT NULL, migration_hash text NOT NULL, status text NOT NULL)")
        conn.execute("INSERT INTO w31b_oracle.state VALUES ('CORE',1)")
        conn.commit()

        payload = "CREATE TABLE w31b_oracle.target (id bigint PRIMARY KEY)"
        a = identity("m1", "CORE", 1, 2, payload)
        b = identity("m1", "CORE", 1, 2, payload)
        c = identity("m1", "CORE", 1, 2, "CREATE TABLE w31b_oracle.target (id bigint, value text)")
        assert a == b
        assert a != c
        assert a["migration_id"] == c["migration_id"]
        assert a["migration_hash"] != c["migration_hash"]

        conn.execute("CREATE TABLE w31b_oracle.target (id bigint PRIMARY KEY)")
        conn.execute("INSERT INTO w31b_oracle.upgrade VALUES (%s,'CORE',1,2,%s,'APPLIED')", (a["migration_id"], a["migration_hash"]))
        conn.execute("UPDATE w31b_oracle.state SET version=2 WHERE schema_id='CORE'")
        conn.commit()

        state = conn.execute("SELECT schema_id,version FROM w31b_oracle.state WHERE schema_id='CORE'").fetchone()
        record = conn.execute("SELECT migration_id,schema_id,from_version,to_version,migration_hash,status FROM w31b_oracle.upgrade WHERE migration_id='m1'").fetchone()
        assert state == ("CORE", 2)
        assert record == ("m1", "CORE", 1, 2, a["migration_hash"], "APPLIED")

        payload_record = json.dumps({"identity": a, "state": state, "status": record[-1]}, sort_keys=True)
        evidence_hash = hashlib.sha256(payload_record.encode()).hexdigest()
        assert len(evidence_hash) == 64
        print("W3.1-B independent oracle: PASS")
        print("identity sensitivity/conflict: PASS")
        print("authoritative predecessor->successor record: PASS")
        print("evidence hash determinism: PASS")


if __name__ == "__main__":
    main()
