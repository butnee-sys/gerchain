import os

import hashlib
import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def _integrity_hash(transaction_id: str, source: str, destination: str, amount: int, currency: str) -> str:
    material = json.dumps(
        {
            "transaction_id": transaction_id,
            "operation": "SETTLEMENT",
            "escrow_id": None,
            "source": source,
            "destination": destination,
            "amount": amount,
            "currency": currency,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def test_production_factory_and_canonical_ledger_postgresql():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, future=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-smoke-escrow",
            amount=100,
            currency="MNT",
            witness_id="pg-smoke-witness",
        ),
        engine=engine,
    ).create()
    assert runtime.is_canonical_ledger_authoritative

    ledger = runtime._canonical_ledger
    assert ledger is not None

    with session_factory() as session:
        ledger.create_account_in_transaction(session, "pg-source", "MNT", 1000)
        ledger.create_account_in_transaction(session, "pg-destination", "MNT", 0)
        session.commit()

    tx_id = "pg-smoke-tx-1"
    integrity_hash = _integrity_hash(tx_id, "pg-source", "pg-destination", 250, "MNT")
    with session_factory() as session:
        result = ledger.transfer_in_transaction(
            session,
            tx_id,
            "pg-source",
            "pg-destination",
            250,
            "MNT",
            operation="SETTLEMENT",
            escrow_id=None,
            integrity_hash=integrity_hash,
        )
        assert result["replayed"] is False
        session.commit()

    with session_factory() as session:
        source = session.get(LedgerAccountModel, "pg-source")
        destination = session.get(LedgerAccountModel, "pg-destination")
        movement = session.execute(
            select(LedgerMovementModel).where(LedgerMovementModel.transaction_id == tx_id)
        ).scalar_one()
        assert source.balance == 750
        assert destination.balance == 250
        assert movement.operation == "SETTLEMENT"
        assert movement.escrow_id is None

        replay = ledger.transfer_in_transaction(
            session,
            tx_id,
            "pg-source",
            "pg-destination",
            250,
            "MNT",
            operation="SETTLEMENT",
            escrow_id=None,
            integrity_hash=integrity_hash,
        )
        assert replay["replayed"] is True
        session.commit()

    with session_factory() as session:
        count = session.execute(
            select(LedgerMovementModel).where(LedgerMovementModel.transaction_id == tx_id)
        ).scalars().all()
        assert len(count) == 1

    engine.dispose()
