"""Explicit production construction for the GerChain durable runtime."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from postgres.migrations import apply_migrations
from persistence.production_schema_guard import assert_canonical_production_schema
from services.gerchain_runtime import GerchainRuntime


@dataclass(frozen=True)
class ProductionRuntimeConfig:
    database_url: str
    escrow_id: str
    amount: int
    currency: str
    witness_id: str


class ProductionRuntimeFactory:
    """Construct the production runtime with Canonical Ledger authority."""

    def __init__(self, config: ProductionRuntimeConfig, *, engine: Engine | None = None) -> None:
        if not config.database_url:
            raise ValueError("database_url is required")
        if not config.database_url.startswith(
            ("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")
        ):
            raise ValueError("ProductionRuntimeFactory requires PostgreSQL database URL")
        self.config = config
        self.engine = engine or create_engine(config.database_url, future=True)
        if self.engine.dialect.name != "postgresql":
            raise ValueError("ProductionRuntimeFactory requires a PostgreSQL engine")
        self.session_factory: Callable[[], Any] = sessionmaker(
            bind=self.engine, expire_on_commit=False
        )

    def initialize(self) -> None:
        """Apply versioned PostgreSQL migrations, then create canonical metadata."""
        schema_dir = Path(__file__).resolve().parents[1] / "postgres" / "schema"
        migrations = []
        for path in sorted(schema_dir.glob("*.sql")):
            try:
                version = int(path.name.split("_", 1)[0])
            except (ValueError, IndexError):
                continue
            migrations.append((version, path))

        with self.engine.begin() as connection:
            connection.execute(text(
                "CREATE TABLE IF NOT EXISTS schema_version ("
                "version BIGINT PRIMARY KEY, checksum TEXT NOT NULL, "
                "applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            ))
            for version, path in migrations:
                sql = path.read_text(encoding="utf-8")
                checksum = sha256(sql.encode("utf-8")).hexdigest()
                existing = connection.execute(
                    text("SELECT checksum FROM schema_version WHERE version = :version"),
                    {"version": version},
                ).scalar_one_or_none()
                if existing is not None:
                    if existing != checksum:
                        raise RuntimeError(f"migration checksum mismatch for version {version}")
                    continue
                connection.exec_driver_sql(sql)
                connection.execute(
                    text("INSERT INTO schema_version(version, checksum) VALUES (:version, :checksum)"),
                    {"version": version, "checksum": checksum},
                )

        for base in (AtomicLedgerBase, EscrowBase, OutboxBase, IdempotencyBase, TransactionWitness):
            base.metadata.create_all(self.engine)

    def create(self) -> GerchainRuntime:
        self.initialize()
        runtime = GerchainRuntime(
            escrow_id=self.config.escrow_id,
            amount=self.config.amount,
            currency=self.config.currency,
            witness_id=self.config.witness_id,
        )
        runtime.configure_canonical_ledger(self.session_factory)
        runtime.require_canonical_ledger_authority()
        return runtime


__all__ = ["ProductionRuntimeConfig", "ProductionRuntimeFactory"]
