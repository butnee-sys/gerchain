from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import Engine, inspect

from postgres.migrations import apply_migrations
from services.gerchain_runtime import GerchainRuntime
from postgres.migrations import apply_migrations


@dataclass(frozen=True)
class ProductionRuntimeConfig:
    """Compatibility configuration contract for production runtime construction."""

    database_url: str
    escrow_id: str
    amount: int
    currency: str
    witness_id: str


class ProductionRuntimeFactory:
    """Create the production GerChain runtime with PostgreSQL as authority."""

    @staticmethod
    def create(
        *,
        escrow_id: str,
        amount: int,
        currency: str,
        witness_id: str,
        engine: Engine,
        session_factory: Callable[[], Any],
        initial_state: dict[str, Any] | None = None,
        manifest: dict[str, Any] | None = None,
        initial_money_state: dict[str, Any] | None = None,
    ) -> GerchainRuntime:
        if engine is None or session_factory is None:
            raise ValueError("production runtime requires PostgreSQL engine and session factory")
        if engine.dialect.name != "postgresql":
            raise ValueError("production runtime requires PostgreSQL engine")

        migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "migrations"
        if not migration_dir.is_dir():
            raise RuntimeError(f"canonical production migration directory not found: {migration_dir}")

        with engine.connect() as connection:
            apply_migrations(connection, migration_dir)

        required = {
            "escrows": {
                "id", "sender_address", "receiver_address", "amount", "state",
                "refund_destination", "currency", "version", "created_at", "updated_at",
            },
            "gerchain_ledger_accounts": {
                "account_id", "currency", "balance", "version", "updated_at",
            },
            "gerchain_ledger_movements": {
                "id", "transaction_id", "source", "destination", "amount",
                "currency", "operation", "escrow_id", "integrity_hash", "created_at",
            },
            "gerchain_transaction_witnesses": {
                "id", "transaction_id", "event_type", "escrow_id", "amount", "created_at",
            },
            "gerchain_outbox_events": {
                "id", "event_id", "event_type", "aggregate_id", "payload_json",
                "state", "lease_until", "attempts", "created_at", "updated_at",
            },
            "gerchain_idempotency_records": {
                "id", "key", "fingerprint", "result_json", "state", "created_at", "updated_at",
            },
        }

        inspector = inspect(engine)
        missing_tables = sorted(set(required) - set(inspector.get_table_names()))
        if missing_tables:
            raise RuntimeError(f"canonical production schema missing tables: {missing_tables}")

        missing_columns: dict[str, list[str]] = {}
        for table, columns in required.items():
            actual = {column["name"] for column in inspector.get_columns(table)}
            missing = sorted(columns - actual)
            if missing:
                missing_columns[table] = missing
        if missing_columns:
            raise RuntimeError(f"canonical production schema missing columns: {missing_columns}")

        runtime = GerchainRuntime(
            escrow_id=escrow_id,
            amount=amount,
            currency=currency,
            witness_id=witness_id,
            initial_state=initial_state,
            manifest=manifest,
            initial_money_state=initial_money_state,
        )
        runtime.configure_canonical_ledger(session_factory)
        runtime.require_canonical_ledger_authority()
        return runtime

__all__ = ["ProductionRuntimeConfig", "ProductionRuntimeFactory"]
