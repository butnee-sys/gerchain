import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.cancel_escrow import cancel_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.settlement_coordinator import SettlementCoordinator
from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)


pytestmark = pytest.mark.postgres


def _database_url() -> str:
    value = os.environ.get("GERCHAIN_TEST_DATABASE_URL") or os.environ.get("GERCHAIN_DATABASE_URL")
    if not value:
        pytest.skip("PostgreSQL test database is not configured")
    return value


def _seed_escrow(session, escrow_id: str, sender: str, amount: int = 40):
    now = datetime.now(timezone.utc)
    session.add(
        CanonicalEscrow(
            id=escrow_id,
            sender_address=sender,
            receiver_address="BENEFICIARY",
            amount=amount,
            state=EscrowState.CREATED.value,
            condition_desc="production-gate",
            refund_destination=sender,
            currency="USD",
            version=0,
            created_at=now,
            updated_at=now,
        )
    )


def test_production_factory_boots_against_real_postgresql():
    url = _database_url()
    engine = create_engine(url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="boot-escrow",
            amount=1,
            currency="USD",
            witness_id="boot-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative
    with engine.connect() as connection:
        assert connection.execute(select(1)).scalar_one() == 1
    engine.dispose()


def test_real_postgresql_full_canonical_value_flow_and_reconciliation():
    url = _database_url()
    engine = create_engine(url, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    runtime_factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="release-escrow",
            amount=40,
            currency="USD",
            witness_id="gate-witness",
        ),
        engine=engine,
    )
    runtime_factory.create()

    with factory() as session:
        for account_id, balance in (
            ("SRC-FUND", 200),
            ("release-escrow", 0),
            ("REFUND-SRC", 100),
            ("refund-escrow", 0),
            ("CANCEL-SRC", 100),
            ("cancel-escrow", 0),
            ("SETTLE-A", 100),
            ("SETTLE-B", 0),
        ):
            session.add(
                LedgerAccountModel(
                    account_id=account_id,
                    currency="USD",
                    balance=balance,
                    version=0,
                    updated_at=datetime.now(timezone.utc),
                )
            )
        _seed_escrow(session, "release-escrow", "SRC-FUND")
        _seed_escrow(session, "refund-escrow", "REFUND-SRC")
        _seed_escrow(session, "cancel-escrow", "CANCEL-SRC")
        session.commit()

    # FUND -> LOCK -> RELEASE
    with factory() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="gate-fund",
            escrow_id="release-escrow",
            source="SRC-FUND",
            amount=40,
            currency="USD",
            payload={"gate": True},
        )
        session.commit()
    with factory() as session:
        lock_escrow_in_transaction(
            session,
            transaction_id="gate-lock",
            escrow_id="release-escrow",
            payload={"gate": True},
        )
        session.commit()
    with factory() as session:
        release_escrow_in_transaction(
            session,
            transaction_id="gate-release",
            escrow_id="release-escrow",
            beneficiary="BENEFICIARY",
            amount=40,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
            payload={"gate": True},
        )
        session.commit()

    # FUND -> LOCK -> REFUND; caller has no authority to change refund destination.
    with factory() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="gate-refund-fund",
            escrow_id="refund-escrow",
            source="REFUND-SRC",
            amount=40,
            currency="USD",
            payload={"gate": True},
        )
        lock_escrow_in_transaction(
            session,
            transaction_id="gate-refund-lock",
            escrow_id="refund-escrow",
            payload={"gate": True},
        )
        refund_escrow_in_transaction(
            session,
            transaction_id="gate-refund",
            escrow_id="refund-escrow",
            amount=40,
            currency="USD",
            payload={"requested_destination": "ATTACKER", "gate": True},
        )
        session.commit()

    # FUND -> CANCEL; reversal returns value to authoritative sender.
    with factory() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="gate-cancel-fund",
            escrow_id="cancel-escrow",
            source="CANCEL-SRC",
            amount=40,
            currency="USD",
            payload={"gate": True},
        )
        cancel_escrow_in_transaction(
            session,
            transaction_id="gate-cancel",
            escrow_id="cancel-escrow",
            payload={"gate": True},
        )
        session.commit()

    # Direct settlement remains coordinated by Canonical Ledger only.
    with factory() as session:
        SettlementCoordinator(session).settle_in_transaction(
            transaction_id="gate-settlement",
            source="SETTLE-A",
            destination="SETTLE-B",
            amount=25,
            currency="USD",
        )
        session.commit()

    with factory() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

        states = {
            row.id: row.state
            for row in session.execute(
                select(CanonicalEscrow).where(
                    CanonicalEscrow.id.in_(
                        ["release-escrow", "refund-escrow", "cancel-escrow"]
                    )
                )
            ).scalars()
        }
        assert states == {
            "release-escrow": "RELEASED",
            "refund-escrow": "REFUNDED",
            "cancel-escrow": "CANCELLED",
        }

        balances = {
            row.account_id: row.balance
            for row in session.execute(
                select(LedgerAccountModel).where(
                    LedgerAccountModel.account_id.in_(
                        [
                            "SRC-FUND",
                            "BENEFICIARY",
                            "REFUND-SRC",
                            "ATTACKER",
                            "CANCEL-SRC",
                            "SETTLE-A",
                            "SETTLE-B",
                        ]
                    )
                )
            ).scalars()
        }
        assert balances["SRC-FUND"] == 160
        assert balances["BENEFICIARY"] == 40
        assert balances["REFUND-SRC"] == 100
        assert "ATTACKER" not in balances
        assert balances["CANCEL-SRC"] == 100
        assert balances["SETTLE-A"] == 75
        assert balances["SETTLE-B"] == 25

    engine.dispose()
