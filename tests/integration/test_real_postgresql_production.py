from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from postgres.migrations import apply_migrations
from persistence.production_schema_guard import assert_canonical_production_schema
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def _reset_database(engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DROP TABLE IF EXISTS
                    gerchain_outbox_events,
                    gerchain_transaction_witnesses,
                    gerchain_idempotency_records,
                    gerchain_ledger_movements,
                    gerchain_ledger_accounts,
                    escrows,
                    outbox,
                    audit_logs,
                    processed_events,
                    schema_version
                CASCADE
                """
            )
        )


def test_real_postgresql_production_lifecycle() -> None:
    database_url = os.environ["TEST_DATABASE_URL"]
    engine = create_engine(database_url, pool_pre_ping=True, future=True)
    _reset_database(engine)

    migration_dir = Path(__file__).resolve().parents[1] / "postgres" / "schema"
    with engine.begin() as connection:
        apply_migrations(connection, migration_dir)
        assert_canonical_production_schema(connection)

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="E-RELEASE",
            amount=40,
            currency="MNT",
            witness_id="w-production",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    now = datetime.now(timezone.utc)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_factory.begin() as session:
        for account_id, balance in {
            "ALICE": 100,
            "CAROL": 100,
            "DAVE": 100,
            "E-RELEASE": 0,
            "E-REFUND": 0,
            "E-CANCEL": 0,
            "BOB": 0,
            "SETTLE": 0,
        }.items():
            session.add(
                LedgerAccountModel(
                    account_id=account_id,
                    currency="MNT",
                    balance=balance,
                    version=0,
                    updated_at=now,
                )
            )
        session.add_all(
            [
                CanonicalEscrow(
                    id="E-RELEASE",
                    sender_address="ALICE",
                    receiver_address="BOB",
                    amount=40,
                    state=EscrowState.CREATED.value,
                    condition_desc="release",
                    refund_destination="ALICE",
                    currency="MNT",
                    version=0,
                    created_at=now,
                    updated_at=now,
                ),
                CanonicalEscrow(
                    id="E-REFUND",
                    sender_address="CAROL",
                    receiver_address="BOB",
                    amount=40,
                    state=EscrowState.CREATED.value,
                    condition_desc="refund",
                    refund_destination="CAROL",
                    currency="MNT",
                    version=0,
                    created_at=now,
                    updated_at=now,
                ),
                CanonicalEscrow(
                    id="E-CANCEL",
                    sender_address="DAVE",
                    receiver_address="BOB",
                    amount=40,
                    state=EscrowState.CREATED.value,
                    condition_desc="cancel",
                    refund_destination="DAVE",
                    currency="MNT",
                    version=0,
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )

    release = runtime
    release.escrow_engine.escrow_id = "E-RELEASE"
    release.fund("FUND-1", "ALICE", "T1", {"verified": True})
    release.lock("LOCK-1", "T2", {"verified": True})
    release.release(
        transaction_id="REL-1",
        destination="BOB",
        timestamp="T3",
        evidence={"verified": True},
        root=object(),
        owner_id="owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )

    release.escrow_engine.escrow_id = "E-REFUND"
    release.fund("FUND-2", "CAROL", "T1", {"verified": True})
    release.lock("LOCK-2", "T2", {"verified": True})
    release.refund(
        transaction_id="REF-1",
        destination="ATTACKER",
        timestamp="T3",
        evidence={"verified": True},
        root=object(),
        owner_id="owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )

    release.escrow_engine.escrow_id = "E-CANCEL"
    release.fund("FUND-3", "DAVE", "T1", {"verified": True})
    release.cancel(transaction_id="CAN-1", timestamp="T2", evidence={"reason": "cancel"})

    release.settle(
        transaction_id="SET-1",
        source="ALICE",
        destination="SETTLE",
        amount=10,
        currency="MNT",
    )

    with session_factory() as session:
        balances = {
            row.account_id: row.balance
            for row in session.query(LedgerAccountModel).all()
        }
        assert balances["ALICE"] == 50
        assert balances["BOB"] == 40
        assert balances["CAROL"] == 100
        assert balances["DAVE"] == 100
        assert balances["SETTLE"] == 10
        assert balances["E-RELEASE"] == 0
        assert balances["E-REFUND"] == 0
        assert balances["E-CANCEL"] == 0

        assert session.get(CanonicalEscrow, "E-RELEASE").state == "RELEASED"
        assert session.get(CanonicalEscrow, "E-REFUND").state == "REFUNDED"
        assert session.get(CanonicalEscrow, "E-CANCEL").state == "CANCELLED"

        report = deep_reconcile_value_truth(session)
        assert report.matched, [issue.code + ":" + issue.detail for issue in report.issues]

    # A second construction must preserve the same canonical production authority.
    restarted = factory.create()
    assert restarted.is_canonical_ledger_authoritative
    engine.dispose()
