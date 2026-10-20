from datetime import datetime, timezone

from sqlalchemy import select

from persistence.atomic_value_transaction import TransactionWitness
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.atomic_ledger import LedgerAccountModel
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_postgresql_production_boot_and_canonical_value_flow():
    database_url = "postgresql+psycopg://gerchain:gerchain@localhost:5432/gerchain"
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="eai-ci-escrow",
            amount=40,
            currency="USD",
            witness_id="eai-ci-witness",
        )
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    now = datetime.now(timezone.utc)
    with factory.session_factory() as session:
        session.add(
            CanonicalEscrow(
                id="eai-ci-escrow",
                sender_address="SRC",
                receiver_address="BENEFICIARY",
                refund_destination="SRC",
                amount=40,
                state=EscrowState.CREATED.value,
                condition_desc="CI production canonical flow",
                currency="USD",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.add_all(
            [
                LedgerAccountModel(
                    account_id="SRC",
                    currency="USD",
                    balance=100,
                    version=0,
                    updated_at=now,
                ),
                LedgerAccountModel(
                    account_id="eai-ci-escrow",
                    currency="USD",
                    balance=0,
                    version=0,
                    updated_at=now,
                ),
                LedgerAccountModel(
                    account_id="BENEFICIARY",
                    currency="USD",
                    balance=0,
                    version=0,
                    updated_at=now,
                ),
            ]
        )
        session.commit()

    with factory.session_factory() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="ci-fund-1",
            escrow_id="eai-ci-escrow",
            source="SRC",
            amount=40,
            currency="USD",
            payload={"ci": "fund"},
        )
        session.commit()

    assert runtime.get_balance("SRC") == 60
    assert runtime.get_balance("eai-ci-escrow") == 40
    assert runtime.get_escrow_state()["state"] == "FUNDED"

    with factory.session_factory() as session:
        lock_escrow_in_transaction(
            session,
            transaction_id="ci-lock-1",
            escrow_id="eai-ci-escrow",
            payload={"ci": "lock"},
        )
        session.commit()

    assert runtime.get_escrow_state()["state"] == "LOCKED"

    with factory.session_factory() as session:
        release_escrow_in_transaction(
            session,
            transaction_id="ci-release-1",
            escrow_id="eai-ci-escrow",
            beneficiary="BENEFICIARY",
            amount=40,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
            payload={"ci": "release"},
        )
        session.commit()

        report = deep_reconcile_value_truth(session)
        assert report.matched, [f"{i.code}:{i.detail}" for i in report.issues]

        witness = session.execute(
            select(TransactionWitness).where(
                TransactionWitness.transaction_id == "ci-release-1"
            )
        ).scalar_one()
        assert witness.event_type == "GERCHAIN_RELEASED"

    assert runtime.get_balance("eai-ci-escrow") == 0
    assert runtime.get_balance("BENEFICIARY") == 40
    assert runtime.get_escrow_state()["state"] == "RELEASED"
