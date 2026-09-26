import os
from datetime import datetime, timezone

from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.atomic_ledger import PostgreSQLAtomicLedger, LedgerAccountModel, LedgerMovementModel
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth


def test_production_postgres_fund_lock_release_reconciles():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-ea35-escrow",
            amount=100,
            currency="USD",
            witness_id="pg-ea35-witness",
        ),
        engine=engine,
    ).create()
    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"
    with factory() as session:
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "pg-source", "USD", initial_balance=100)
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "pg-beneficiary", "USD", initial_balance=0)
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "pg-ea35-escrow", "USD", initial_balance=0)
        session.add(CanonicalEscrow(
            id="pg-ea35-escrow",
            sender_address="pg-source",
            receiver_address="pg-beneficiary",
            amount=100,
            state=EscrowState.CREATED.value,
            condition_desc="production integration",
            refund_destination="pg-source",
            currency="USD",
            version=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ))
        session.commit()

    with factory() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="pg-fund-1",
            escrow_id="pg-ea35-escrow",
            source="pg-source",
            amount=100,
            currency="USD",
        )
        session.commit()

    with factory() as session:
        lock_escrow_in_transaction(
            session,
            transaction_id="pg-lock-1",
            escrow_id="pg-ea35-escrow",
        )
        session.commit()

    with factory() as session:
        release_escrow_in_transaction(
            session,
            transaction_id="pg-release-1",
            escrow_id="pg-ea35-escrow",
            beneficiary="pg-beneficiary",
            amount=100,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        session.commit()

    with factory() as session:
        balances = {
            row.account_id: row.balance
            for row in session.execute(select(LedgerAccountModel)).scalars()
        }
        escrow = session.get(CanonicalEscrow, "pg-ea35-escrow")
        report = deep_reconcile_value_truth(session)
        assert balances["pg-source"] == 0
        assert balances["pg-beneficiary"] == 100
        assert escrow.state == EscrowState.RELEASED.value
        assert report.matched, [f"{i.code}: {i.detail}" for i in report.issues]

    engine.dispose()


def test_production_postgres_restart_does_not_duplicate_release() -> None:
    url = os.environ["GERCHAIN_DATABASE_URL"]
    escrow_id = "pg-ea35-restart-escrow"
    engine = create_engine(url, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id=escrow_id,
            amount=50,
            currency="USD",
            witness_id="pg-ea35-restart-witness",
        ),
        engine=engine,
    ).create()

    now = datetime.now(timezone.utc)
    with factory.begin() as session:
        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, "pg-restart-source", "USD", initial_balance=50
        )
        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, escrow_id, "USD", initial_balance=0
        )
        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, "pg-restart-beneficiary", "USD", initial_balance=0
        )
        session.add(CanonicalEscrow(
            id=escrow_id,
            sender_address="pg-restart-source",
            receiver_address="pg-restart-beneficiary",
            amount=50,
            state=EscrowState.CREATED.value,
            condition_desc="restart replay proof",
            refund_destination="pg-restart-source",
            currency="USD",
            version=0,
            created_at=now,
            updated_at=now,
        ))

    runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id=escrow_id,
            amount=50,
            currency="USD",
            witness_id="pg-ea35-restart-witness",
        ),
        engine=engine,
    ).create()
    runtime.fund("pg-restart-fund", "pg-restart-source", "T0", {"proof": "restart"})
    runtime.lock("pg-restart-lock", "T1", {"proof": "restart"})
    first = runtime.release(
        root=object(),
        owner_id="pg-restart-owner",
        transaction_id="pg-restart-release",
        destination="pg-restart-beneficiary",
        authorized=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
        evidence_verified=True,
        timestamp="T2",
        evidence={"proof": "restart"},
    )
    assert first["replayed"] is False
    engine.dispose()

    restarted_engine = create_engine(url, pool_pre_ping=True)
    restarted_factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id=escrow_id,
            amount=50,
            currency="USD",
            witness_id="pg-ea35-restart-witness",
        ),
        engine=restarted_engine,
    )
    runtime_again = restarted_factory.create()  # construction itself is the restart boundary
    result = runtime_again.release(
        root=object(),
        owner_id="pg-restart-owner",
        transaction_id="pg-restart-release",
        destination="pg-restart-beneficiary",
        authorized=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
        evidence_verified=True,
        timestamp="T2",
        evidence={"proof": "restart"},
    )
    assert result["replayed"] is True

    with sessionmaker(bind=restarted_engine, expire_on_commit=False)() as session:
        source = session.get(LedgerAccountModel, "pg-restart-source")
        beneficiary = session.get(LedgerAccountModel, "pg-restart-beneficiary")
        escrow = session.get(CanonicalEscrow, escrow_id)
        movements = session.execute(select(LedgerMovementModel)).scalars().all()
        report = deep_reconcile_value_truth(session)

        assert source.balance == 0
        assert beneficiary.balance == 50
        assert escrow.state == EscrowState.RELEASED.value
        assert len(movements) == 2
        assert report.matched, [f"{i.code}: {i.detail}" for i in report.issues]

    restarted_engine.dispose()
