from __future__ import annotations

from sqlalchemy import text


REQUIRED_TABLES = {
    "schema_version",
    "escrows",
    "gerchain_ledger_accounts",
    "gerchain_ledger_movements",
    "gerchain_transaction_witnesses",
    "gerchain_outbox_events",
    "gerchain_idempotency_records",
}

REQUIRED_COLUMNS = {
    "gerchain_ledger_movements": {"operation", "escrow_id", "integrity_hash"},
    "escrows": {"refund_destination", "currency", "version", "created_at"},
}


def assert_canonical_production_schema(connection) -> None:
    """Fail closed unless the PostgreSQL canonical production schema is complete."""
    tables = {
        row[0]
        for row in connection.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        ).fetchall()
    }
    missing_tables = sorted(REQUIRED_TABLES - tables)
    if missing_tables:
        raise RuntimeError(f"canonical production schema missing tables: {missing_tables}")

    for table, required in REQUIRED_COLUMNS.items():
        columns = {
            row[0]
            for row in connection.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=:table"),
                {"table": table},
            ).fetchall()
        }
        missing = sorted(required - columns)
        if missing:
            raise RuntimeError(f"canonical production schema missing {table} columns: {missing}")

    versions = [
        int(row[0])
        for row in connection.execute(
            text("SELECT version FROM schema_version ORDER BY version")
        ).fetchall()
    ]
    if versions != list(range(1, 6)):
        raise RuntimeError(f"canonical production schema migration set is incomplete: {versions}")


__all__ = ["assert_canonical_production_schema"]
