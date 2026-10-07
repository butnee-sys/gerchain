from __future__ import annotations

import os
import signal
import time

from sqlalchemy import create_engine

from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)


_running = True


def _stop(*_args) -> None:
    global _running
    _running = False


def build_production_runtime():
    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not database_url or not database_url.startswith("postgresql"):
        raise RuntimeError(
            "production entrypoint requires GERCHAIN_DATABASE_URL pointing to PostgreSQL"
        )

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
    except ValueError as exc:
        raise RuntimeError("GERCHAIN_ESCROW_AMOUNT must be an integer") from exc

    engine = create_engine(database_url, pool_pre_ping=True)
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
        engine.dispose()
        raise RuntimeError("canonical ledger authority was not established")

    return runtime, engine


def build_production_runtime():
    """Build the canonical production runtime from environment configuration."""
    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    escrow_id = os.environ.get("GERCHAIN_ESCROW_ID")
    currency = os.environ.get("GERCHAIN_CURRENCY")
    witness_id = os.environ.get("GERCHAIN_WITNESS_ID")
    amount_raw = os.environ.get("GERCHAIN_ESCROW_AMOUNT")
    if not database_url or not database_url.startswith("postgresql"):
        raise RuntimeError("production entrypoint requires PostgreSQL GERCHAIN_DATABASE_URL")
    if not all((escrow_id, currency, witness_id, amount_raw)):
        raise RuntimeError("production entrypoint requires escrow, amount, currency, and witness configuration")
    try:
        amount = int(amount_raw)
    except ValueError as exc:
        raise RuntimeError("GERCHAIN_ESCROW_AMOUNT must be an integer") from exc
    engine = create_engine(database_url, pool_pre_ping=True)
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
    return factory.create(), engine


def main() -> None:
    runtime, engine = build_production_runtime()
    escrow_id = runtime.escrow_engine.escrow_id
    currency = runtime.escrow_engine.currency

    print(
        "GerChain production runtime initialized: "
        f"escrow={escrow_id} currency={currency}"
    )

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    try:
        while _running:
            time.sleep(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
