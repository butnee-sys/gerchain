from datetime import datetime, timezone
from uuid import uuid4

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import DurableIdempotencyRecord, IdempotencyBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.recovery_outbox import OutboxBase
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory
from persistence.cancel_escrow import cancel_escrow_in_transaction
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.settlement_coordinator import SettlementCoordinator


def _factory():
    import os

    url = os.environ["GERCHAIN_POSTGRES_DSN"]
    engine = create_engine(url, future=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="escrow-1",
            amount=40,
            currency="USD",
            witness_id="witness-ea3513",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def test_canonical_postgres_transaction_and_deep_truth():
    engine, factory = _factory()
    now = datetime.now(timezone.utc)

    with factory() as session:
        ledger = PostgreSQLAtomicLedger(factory)
        ledger.create_account_in_transaction(session, "SRC", "USD", 60)
        ledger.create_account_in_transaction(session, "escrow-1", "USD", 40)
        ledger.create_account_in_transaction(session, "BENEFICIARY", "USD", 0)

        session.add(
            CanonicalEscrow(
                id="escrow-1",
                sender_address="SRC",
                receiver_address="BENEFICIARY",
                refund_destination="SRC",
                amount=40,
                state=EscrowState.LOCKED.value,
                condition_desc="postgres canonical gate",
                currency="USD",
                version=2,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

        from persistence.release_escrow import release_escrow_in_transaction

        result = release_escrow_in_transaction(
            session,
            transaction_id="pg-release-1",
            escrow_id="escrow-1",
            beneficiary="BENEFICIARY",
            amount=40,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
            payload={"gate": "EA-35.13"},
        )
        session.commit()

        assert result["replayed"] is False
        assert session.execute(
            select(LedgerAccountModel).where(LedgerAccountModel.account_id == "SRC")
        ).scalar_one().balance == 60
        assert session.execute(
            select(LedgerAccountModel).where(
                LedgerAccountModel.account_id == "BENEFICIARY"
            )
        ).scalar_one().balance == 40

        report = deep_reconcile_value_truth(session)
        assert report.matched, [f"{i.code}: {i.detail}" for i in report.issues]

        movement = session.execute(
            select(LedgerAccountModel).where(LedgerAccountModel.account_id == "escrow-1")
        ).scalar_one()
        assert movement.balance == 0

    engine.dispose()


def test_eai_production_full_value_flow_reperformance():
    engine, factory = _factory()
    suffix = uuid4().hex

    release_id = f"release-{suffix}"
    refund_id = f"refund-{suffix}"
    cancel_id = f"cancel-{suffix}"
    created_cancel_id = f"created-cancel-{suffix}"

    source = f"source-{suffix}"
    beneficiary = f"beneficiary-{suffix}"
    refund_source = f"refund-source-{suffix}"
    cancel_source = f"cancel-source-{suffix}"
    settlement_source = f"settlement-source-{suffix}"
    settlement_destination = f"settlement-destination-{suffix}"

    with factory() as session:
        ledger = PostgreSQLAtomicLedger(factory)
        for account_id, balance in (
            (source, 100), (release_id, 0), (beneficiary, 0), (refund_source, 100),
            (refund_id, 0), (cancel_source, 100), (cancel_id, 0),
            (settlement_source, 50), (settlement_destination, 0),
        ):
            ledger.create_account_in_transaction(session, account_id, "USD", balance)

        now = datetime.now(timezone.utc)
        for escrow_id, sender, receiver, amount in (
            (release_id, source, beneficiary, 40),
            (refund_id, refund_source, f"unused-{refund_id}", 30),
            (cancel_id, cancel_source, f"unused-{cancel_id}", 20),
            (created_cancel_id, f"created-{created_cancel_id}", f"unused-{created_cancel_id}", 10),
        ):
            session.add(CanonicalEscrow(
                id=escrow_id, sender_address=sender, receiver_address=receiver,
                refund_destination=sender, amount=amount,
                state=EscrowState.CREATED.value,
                condition_desc="EAI production re-performance", currency="USD",
                version=0, created_at=now, updated_at=now,
            ))
        session.commit()

        fund_escrow_in_transaction(session, transaction_id=f"fund-{release_id}",
            escrow_id=release_id, source=source, amount=40, currency="USD")
        lock_escrow_in_transaction(session, transaction_id=f"lock-{release_id}", escrow_id=release_id)
        release_escrow_in_transaction(session, transaction_id=f"release-{release_id}",
            escrow_id=release_id, beneficiary=beneficiary, amount=40, currency="USD",
            decision_status="APPROVE", authorization_status="AUTHORIZED",
            trust=True, transparency=True, performance=True, evidence_verified=True)

        fund_escrow_in_transaction(session, transaction_id=f"fund-{refund_id}",
            escrow_id=refund_id, source=refund_source, amount=30, currency="USD")
        lock_escrow_in_transaction(session, transaction_id=f"lock-{refund_id}", escrow_id=refund_id)
        refund_escrow_in_transaction(session, transaction_id=f"refund-{refund_id}",
            escrow_id=refund_id, amount=30, currency="USD")

        fund_escrow_in_transaction(session, transaction_id=f"fund-{cancel_id}",
            escrow_id=cancel_id, source=cancel_source, amount=20, currency="USD")
        cancel_escrow_in_transaction(session, transaction_id=f"cancel-{cancel_id}", escrow_id=cancel_id)
        cancel_escrow_in_transaction(session, transaction_id=f"cancel-{created_cancel_id}",
            escrow_id=created_cancel_id)

        SettlementCoordinator(session).settle_in_transaction(
            transaction_id=f"settle-{settlement_source}",
            source=settlement_source, destination=settlement_destination,
            amount=15, currency="USD")
        session.commit()

        states = {e.id: e.state for e in session.execute(
            select(CanonicalEscrow).where(
                CanonicalEscrow.id.in_([release_id, refund_id, cancel_id, created_cancel_id])
            )
        ).scalars()}
        assert states[release_id] == EscrowState.RELEASED.value
        assert states[refund_id] == EscrowState.REFUNDED.value
        assert states[cancel_id] == EscrowState.CANCELLED.value
        assert states[created_cancel_id] == EscrowState.CANCELLED.value

        balances = {row.account_id: row.balance for row in session.execute(
            select(LedgerAccountModel)
        ).scalars()}
        assert balances[source] == 60
        assert balances[beneficiary] == 40
        assert balances[refund_source] == 100
        assert balances[refund_id] == 0
        assert balances[cancel_source] == 100
        assert balances[cancel_id] == 0
        assert balances[settlement_source] == 35
        assert balances[settlement_destination] == 15

        report = deep_reconcile_value_truth(session)
        assert report.matched, [f"{i.code}: {i.detail}" for i in report.issues]

    engine.dispose()
