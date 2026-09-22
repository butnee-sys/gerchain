from __future__ import annotations

import os
import signal
import time

from services.gerchain_runtime_factory import ProductionRuntimeFactory

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_running = True


def _stop(*_args) -> None:
    global _running
    _running = False


def main() -> None:
    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not database_url or not database_url.startswith("postgresql"):
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
    except ValueError as exc:
        raise RuntimeError("GERCHAIN_ESCROW_AMOUNT must be an integer") from exc

    engine = create_engine(database_url, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    runtime = ProductionRuntimeFactory.create(
        escrow_id=escrow_id,
        amount=amount,
        currency=currency,
        witness_id=witness_id,
        engine=engine,
        session_factory=session_factory,
    )
    if not runtime.is_canonical_ledger_authoritative:
        raise RuntimeError("canonical ledger authority was not established")

    print(
        "GerChain production runtime initialized: "
        f"escrow={escrow_id} currency={currency}"
    )

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    while _running:
        time.sleep(1)

    engine.dispose()


if __name__ == "__main__":
    main(    runtime = ProductionRuntimeFactory.create(
        escrow_id=escrow_id,
        amount=amount,
        currency=currency,
        witness_id=witness_id,
        engine=engine,
        session_factory=session_factory,
    ))