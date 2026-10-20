from __future__ import annotations

import os
from pathlib import Path

import psycopg
import signal
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from postgres.migrations import apply_migrations
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory

_running = True


def _stop(*_args) -> None:
    global _running
    _running = False


def build_production_runtime():
    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not database_url or not database_url.startswith(
        ("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")
    ):
        raise RuntimeError("production entrypoint requires GERCHAIN_DATABASE_URL pointing to PostgreSQL")

    escrow_id = os.environ.get("GERCHAIN_ESCROW_ID")
    currency = os.environ.get("GERCHAIN_CURRENCY")
    witness_id = os.environ.get("GERCHAIN_WITNESS_ID")
    amount_raw = os.environ.get("GERCHAIN_ESCROW_AMOUNT")
    if not all((escrow_id, currency, witness_id, amount_raw)):
        raise RuntimeError(
            "production entrypoint requires GERCHAIN_ESCROW_ID, "
            "GERCHAIN_ESCROW_AMOUNT, GERCHAIN_CURRENCY, and GERCHAIN_WITNESS_ID"
        )

    try:
        amount = int(amount_raw)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("GERCHAIN_ESCROW_AMOUNT must be a positive integer") from exc
    if amount <= 0:
        raise RuntimeError("GERCHAIN_ESCROW_AMOUNT must be a positive integer")

    engine = create_engine(database_url, pool_pre_ping=True, future=True)
    try:
        if engine.dialect.name != "postgresql":
            raise RuntimeError("production entrypoint requires a PostgreSQL engine")
        with engine.connect() as connection:
            if connection.exec_driver_sql("SELECT 1").scalar() != 1:
                raise RuntimeError("PostgreSQL readiness probe failed")
        # Apply the canonical, checksummed migration chain before ORM bootstrap.
        migration_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
        with psycopg.connect(migration_url) as migration_connection:
            apply_migrations(
                migration_connection,
                Path(__file__).resolve().parent / "postgres" / "migrations",
            )
        factory = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=database_url,
                escrow_id=escrow_id,
                amount=amount,
                currency=currency,
                witness_id=witness_id,
            ),
            engine=engine,
        )
        runtime = factory.create()
        if not runtime.is_canonical_ledger_authoritative:
            raise RuntimeError("canonical ledger authority was not established")
        return runtime, engine
    except Exception:
        engine.dispose()
        raise


def main() -> None:
    runtime, engine = build_production_runtime()
    print(
        "GerChain production runtime initialized: "
        f"mode={runtime.runtime_mode} escrow={runtime.escrow_engine.escrow_id} "
        f"currency={runtime.escrow_engine.currency} canonical_ledger=authoritative"
    )
    global _running
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    try:
        while _running:
            time.sleep(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
