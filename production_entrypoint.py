from __future__ import annotations

# EA-35.27: migration bootstrap corrected; rerun production PostgreSQL evidence.

import os
import signal
import time

from sqlalchemy import create_engine
from services.gerchain_runtime_factory import ProductionRuntimeFactory

# EA-35.30: production boot verification marker; authority must be canonical.


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
    runtime_factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id=escrow_id,
            amount=amount,
            currency=currency,
            witness_id=witness_id,
        ),
        engine=engine,
    )
    runtime = runtime_factory.create()

    if not runtime.is_canonical_ledger_authoritative:
        raise RuntimeError("canonical ledger authority was not established")

    return runtime, engine


def main() -> None:
    runtime, engine = build_production_runtime()
    print(
        "GerChain production runtime initialized: "
        f"escrow={runtime.escrow_engine.escrow_id} currency={runtime.escrow_engine.currency}"
    )

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    try:
        while _running:
            time.sleep(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()    runtime = ProductionRuntimeFactory.create(
        escrow_id=escrow_id,
        amount=amount,
        currency=currency,
        witness_id=witness_id,
        engine=engine,
        session_factory=session_factory,
    )

    if not runtime.is_canonical_ledger_authoritative:
        raise RuntimeError("canonical ledger authority was not established")

    return runtime, engine


def main() -> None:
    runtime, engine = build_production_runtime()
    print(
        "GerChain production runtime initialized: "
        f"escrow={runtime.escrow_engine.escrow_id} currency={runtime.escrow_engine.currency}"
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
