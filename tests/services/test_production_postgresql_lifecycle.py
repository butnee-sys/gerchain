from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from persistence.atomic_ledger import LedgerAccountModel, PostgreSQLAtomicLedger, LedgerMovementModel
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.atomic_value_transaction import TransactionWitness
from persistence.recovery_outbox import OutboxEvent
from persistence.durable_idempotency import DurableIdempotencyRecord
from services.gerchain_runtime_factory import ProductionRuntimeFactory


def test_production_postgresql_fund_lock_release_truth_graph(
    canonical_postgresql_engine,
):
    runtime = ProductionRuntimeFactory.from_engine(
        escrow_id="production-lifecycle-escrow",
        amount=100,
        currency="MNT",
        witness_id="production-lifecycle-witness",
        engine=canonical_postgresql_engine,
    )
    assert runtime.is_canonical_ledger_authoritative

    from sqlalchemy.orm import sessionmaker
    session_factory = sessionmaker(
        bind=canonical_postgresql_engine,
        expire_on_commit=False,
    )

    with session_factory() as session:
        now = datetime.now(timezone.utc)
        session.add_all([
            LedgerAccountModel(
                account_id="production-source",
                currency="MNT",
                balance=100,
                version=0,
                updated_at=now,
            ),
            LedgerAccountModel(
                account_id="production-lifecycle-escrow",
                currency="MNT",
                balance=0,
                version=0,
                updated_at=now,
            ),
            LedgerAccountModel(
                account_id="production-beneficiary",
                currency="MNT",
                balance=0,
                version=0,
                updated_at=now,
            ),
            CanonicalEscrow(
                id="production-lifecycle-escrow",
                sender_address="production-source",
                receiver_address="production-beneficiary",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="production-smoke",
                refund_destination="production-source",
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            ),
        ])
        session.commit()

        fund_escrow_in_transaction(
            session,
            transaction_id="production-fund-1",
            escrow_id="production-lifecycle-escrow",
            source="production-source",
            amount=100,
            currency="MNT",
        )
        session.commit()

        lock_escrow_in_transaction(
            session,
            transaction_id="production-lock-1",
            escrow_id="production-lifecycle-escrow",
        )
        session.commit()

        release_escrow_in_transaction(
            session,
            transaction_id="production-release-1",
            escrow_id="production-lifecycle-escrow",
            beneficiary="production-beneficiary",
            amount=100,
            currency="MNT",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        session.commit()

        escrow = session.execute(
            select(CanonicalEscrow).where(
                CanonicalEscrow.id == "production-lifecycle-escrow"
            )
        ).scalar_one()
        balances = {
            row.account_id: row.balance
            for row in session.execute(
                select(LedgerAccountModel).where(
                    LedgerAccountModel.account_id.in_([
                        "production-source",
                        "production-lifecycle-escrow",
                        "production-beneficiary",
                    ])
                )
            ).scalars()
        }

        assert escrow.state == EscrowState.RELEASED.value
        assert balances == {
            "production-source": 0,
            "production-lifecycle-escrow": 0,
            "production-beneficiary": 100,
        }
        assert session.execute(select(LedgerMovementModel)).scalars().all()
        assert len(session.execute(select(TransactionWitness)).scalars().all()) == 3
        assert len(session.execute(select(OutboxEvent)).scalars().all()) == 3
        assert len(session.execute(select(DurableIdempotencyRecord)).scalars().all()) == 3
