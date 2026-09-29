from __future__ import annotations

from sqlalchemy import inspect


REQUIRED_COLUMNS = {
    "escrows": {
        "id",
        "sender_address",
        "receiver_address",
        "amount",
        "state",
        "condition_desc",
        "refund_destination",
        "currency",
        "version",
        "created_at",
        "updated_at",
    },
    "gerchain_ledger_accounts": {
        "account_id",
        "currency",
        "balance",
        "version",
        "updated_at",
    },
    "gerchain_ledger_movements": {
        "id",
        "transaction_id",
        "source",
        "destination",
        "amount",
        "currency",
        "operation",
        "escrow_id",
        "integrity_hash",
        "created_at",
    },
    "gerchain_transaction_witnesses": {
        "id",
        "transaction_id",
        "event_type",
        "escrow_id",
        "amount",
        "created_at",
    },
    "gerchain_outbox_events": {
        "id",
        "event_id",
        "event_type",
        "aggregate_id",
        "payload_json",
        "state",
        "lease_until",
        "attempts",
        "created_at",
        "updated_at",
    },
    "gerchain_idempotency_records": {
        "id",
        "key",
        "fingerprint",
        "result_json",
        "state",
        "created_at",
        "updated_at",
    },
}


def assert_canonical_production_schema(engine) -> None:
    """Fail closed unless every canonical production table/column exists."""
    if engine.dialect.name != "postgresql":
        raise RuntimeError("canonical production schema requires PostgreSQL")

    inspector = inspect(engine)
    missing: list[str] = []

    existing_tables = set(inspector.get_table_names())
    for table, columns in REQUIRED_COLUMNS.items():
        if table not in existing_tables:
            missing.append(f"{table} (table)")
            continue
        existing_columns = {column["name"] for column in inspector.get_columns(table)}
        for column in sorted(columns - existing_columns):
            missing.append(f"{table}.{column}")

    if missing:
        raise RuntimeError(
            "canonical production schema incomplete; migration required: "
            + ", ".join(missing)
        )


__all__ = ["REQUIRED_COLUMNS", "assert_canonical_production_schema"]
