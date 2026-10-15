from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg

DSN = os.environ["GERCHAIN_POSTGRES_DSN"]
OUT = Path("postgres-evidence")
OUT.mkdir(parents=True, exist_ok=True)


def write_json(name: str, value: object) -> str:
    raw = (json.dumps(value, sort_keys=True, indent=2, default=str) + "\n").encode("utf-8")
    (OUT / name).write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


with psycopg.connect(DSN) as conn:
    migration_rows = conn.execute(
        "SELECT version, checksum, applied_at FROM schema_version ORDER BY version"
    ).fetchall()
    constraints = conn.execute(
        """
        SELECT n.nspname AS schema_name,
               t.relname AS table_name,
               c.conname AS constraint_name,
               c.contype AS constraint_type,
               pg_get_constraintdef(c.oid, true) AS definition,
               c.convalidated AS validated
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = current_schema()
          AND t.relname = ANY(%s)
        ORDER BY t.relname, c.conname
        """,
        (["schema_version", "escrows", "audit_logs", "outbox", "processed_events"],),
    ).fetchall()

migration_hash = write_json(
    "migration-history.json",
    [
        {"version": int(v), "checksum": checksum, "applied_at": applied_at.isoformat()}
        for v, checksum, applied_at in migration_rows
    ],
)
constraint_hash = write_json(
    "constraint-snapshot.json",
    [
        {
            "schema": schema_name,
            "table": table_name,
            "name": constraint_name,
            "type": constraint_type,
            "definition": definition,
            "validated": validated,
        }
        for schema_name, table_name, constraint_name, constraint_type, definition, validated in constraints
    ],
)
manifest = {
    "evidence_scope": "postgres/tests/test_concurrency.py; legacy concurrency schema only",
    "git_sha": os.environ.get("GITHUB_SHA", "unknown"),
    "workflow_run_id": os.environ.get("GITHUB_RUN_ID", "unknown"),
    "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "unknown"),
    "captured_at_utc": datetime.now(timezone.utc).isoformat(),
    "postgres_server_version": None,
    "migration_history_rows": len(migration_rows),
    "constraint_rows": len(constraints),
    "files": {
        "migration-history.json": migration_hash,
        "constraint-snapshot.json": constraint_hash,
    },
}
with psycopg.connect(DSN) as conn:
    manifest["postgres_server_version"] = conn.execute("SHOW server_version").fetchone()[0]
manifest_hash = write_json("manifest.json", manifest)
(OUT / "manifest.sha256").write_text(f"{manifest_hash}  manifest.json\n", encoding="utf-8")
print(json.dumps({"manifest_sha256": manifest_hash, **manifest}, sort_keys=True))
