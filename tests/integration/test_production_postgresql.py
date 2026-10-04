import hashlib
import json
import os

from persistence.atomic_ledger import LedgerMovementModel, PostgreSQLAtomicLedger
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_postgresql_factory_and_canonical_ledger():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-proof-escrow",
            amount=100,
            currency="USD",
            witness_id="pg-proof-witness",
        )
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    with factory.session_factory() as session:
        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, "pg-proof-source", "USD", 1000
        )
        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, "pg-proof-dest", "USD", 0
        )
        session.commit()

        integrity_material = json.dumps({
            "transaction_id": "pg-proof-tx",
            "operation": "SETTLEMENT",
            "escrow_id": None,
            "source": "pg-proof-source",
            "destination": "pg-proof-dest",
            "amount": 100,
            "currency": "USD",
        }, sort_keys=True, separators=(",", ":"))
        integrity_hash = hashlib.sha256(integrity_material.encode("utf-8")).hexdigest()

        result = PostgreSQLAtomicLedger.transfer_in_transaction(
            session,
            "pg-proof-tx",
            "pg-proof-source",
            "pg-proof-dest",
            100,
            "USD",
            operation="SETTLEMENT",
            integrity_hash=integrity_hash,
        )
        session.commit()

        assert result["replayed"] is False
        movement = session.query(LedgerMovementModel).filter_by(
            transaction_id="pg-proof-tx"
        ).one()
        assert movement.operation == "SETTLEMENT"
        assert session.query(LedgerMovementModel).filter_by(
            transaction_id="pg-proof-tx"
        ).count() == 1
