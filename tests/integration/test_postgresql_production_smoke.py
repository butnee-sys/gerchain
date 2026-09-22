import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel
from services.gerchain_runtime_factory import ProductionRuntimeFactory


def test_production_factory_and_canonical_ledger_postgresql():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, future=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    runtime = ProductionRuntimeFactory.create(
        escrow_id="pg-smoke-escrow",
        amount=100,
        currency="MNT",
        witness_id="pg-smoke-witness",
        engine=engine,
        session_factory=session_factory,
    )
    assert runtime.is_canonical_ledger_authoritative

    ledger = runtime._canonical_ledger
    assert ledger is not None

    with session_factory() as session:
        ledger.create_account_in_transaction(session, "pg-source", "MNT", 1000)
        ledger.create_account_in_transaction(session, "pg-destination", "MNT", 0)
        session.commit()

    with session_factory() as session:
        result = ledger.transfer_in_transaction(
            session,
            "pg-smoke-tx-1",
            "pg-source",
            "pg-destination",
            250,
            "MNT",
            operation="SETTLEMENT",
            escrow_id="pg-smoke-escrow",
            integrity_hash="smoke-hash",
        )
        assert result["replayed"] is False
        session.commit()

    with session_factory() as session:
        source = session.get(LedgerAccountModel, "pg-source")
        destination = session.get(LedgerAccountModel, "pg-destination")
        movement = session.execute(
            select(LedgerMovementModel).where(LedgerMovementModel.transaction_id == "pg-smoke-tx-1")
        ).scalar_one()
        assert source.balance == 750
        assert destination.balance == 250
        assert movement.operation == "SETTLEMENT"
        assert movement.escrow_id == "pg-smoke-escrow"

        replay = ledger.transfer_in_transaction(
            session,
            "pg-smoke-tx-1",
            "pg-source",
            "pg-destination",
            250,
            "MNT",
            operation="SETTLEMENT",
            escrow_id="pg-smoke-escrow",
            integrity_hash="smoke-hash",
        )
        assert replay["replayed"] is True
        session.commit()

    with session_factory() as session:
        count = session.execute(
            select(LedgerMovementModel).where(LedgerMovementModel.transaction_id == "pg-smoke-tx-1")
        ).scalars().all()
        assert len(count) == 1

    engine.dispose()
