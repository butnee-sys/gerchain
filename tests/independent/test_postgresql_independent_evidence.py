from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_independent_postgresql_persisted_value_evidence() -> None:
    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not database_url:
        raise RuntimeError("GERCHAIN_DATABASE_URL is required")

    engine = create_engine(database_url, pool_pre_ping=True, future=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="independent-escrow",
            amount=25,
            currency="USD",
            witness_id="independent-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    with engine.begin() as connection:
        connection.execute(text(
            "TRUNCATE TABLE gerchain_outbox_events, gerchain_transaction_witnesses, "
            "gerchain_idempotency_records, gerchain_ledger_movements, "
            "gerchain_ledger_accounts, escrows CASCADE"
        ))

    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    with sessions.begin() as session:
        session.add_all([
            LedgerAccountModel(account_id="independent-source", currency="USD", balance=100, version=0, updated_at=now),
            LedgerAccountModel(account_id="independent-escrow", currency="USD", balance=0, version=0, updated_at=now),
            LedgerAccountModel(account_id="independent-beneficiary", currency="USD", balance=0, version=0, updated_at=now),
        ])
        session.add(CanonicalEscrow(
            id="independent-escrow",
            sender_address="independent-source",
            receiver_address="independent-beneficiary",
            refund_destination="independent-source",
            amount=25,
            currency="USD",
            state=EscrowState.CREATED.value,
            condition_desc="independent evidence",
            version=0,
            created_at=now,
            updated_at=now,
        ))

    runtime.fund("ind-fund", "independent-source", now.isoformat(), {"evidence": "independent"})
    runtime.lock("ind-lock", now.isoformat(), {"evidence": "independent"})
    runtime.release(
        transaction_id="ind-release",
        destination="independent-beneficiary",
        timestamp=now.isoformat(),
        evidence={"evidence": "independent"},
        root=object(),
        owner_id="independent-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )

    # Independent verification path: raw persisted facts only.
    with engine.connect() as connection:
        balances = {
            row.account_id: row.balance
            for row in connection.execute(text(
                "SELECT account_id, balance FROM gerchain_ledger_accounts "
                "WHERE account_id IN ('independent-source','independent-escrow','independent-beneficiary') "
                "ORDER BY account_id"
            ))
        }
        assert balances == {
            "independent-beneficiary": 25,
            "independent-escrow": 0,
            "independent-source": 75,
        }

        movement = connection.execute(text(
            "SELECT transaction_id, operation, escrow_id, source, destination, amount, currency, integrity_hash "
            "FROM gerchain_ledger_movements ORDER BY id"
        )).mappings().all()
        assert [(r["transaction_id"], r["operation"], r["escrow_id"], r["source"], r["destination"], r["amount"], r["currency"]) for r in movement] == [
            ("ind-fund", "FUND", "independent-escrow", "independent-source", "independent-escrow", 25, "USD"),
            ("ind-release", "RELEASE", "independent-escrow", "independent-escrow", "independent-beneficiary", 25, "USD"),
        ]
        assert all(len(r["integrity_hash"]) == 64 for r in movement)

        escrow = connection.execute(text(
            "SELECT state, version, sender_address, receiver_address, refund_destination "
            "FROM escrows WHERE id = 'independent-escrow'"
        )).mappings().one()
        assert dict(escrow) == {
            "state": "RELEASED",
            "version": 3,
            "sender_address": "independent-source",
            "receiver_address": "independent-beneficiary",
            "refund_destination": "independent-source",
        }

        witness = connection.execute(text(
            "SELECT transaction_id, event_type, escrow_id, amount "
            "FROM gerchain_transaction_witnesses ORDER BY id"
        )).mappings().all()
        assert [(r["transaction_id"], r["event_type"], r["escrow_id"], r["amount"]) for r in witness] == [
            ("ind-fund", "GERCHAIN_FUNDED", "independent-escrow", 25),
            ("ind-lock", "GERCHAIN_LOCKED", "independent-escrow", 0),
            ("ind-release", "GERCHAIN_RELEASED", "independent-escrow", 25),
        ]

        outbox = connection.execute(text(
            "SELECT event_type, aggregate_id FROM gerchain_outbox_events ORDER BY id"
        )).all()
        assert [(r[0], r[1]) for r in outbox] == [
            ("GERCHAIN_FUNDED", "independent-escrow"),
            ("GERCHAIN_LOCKED", "independent-escrow"),
            ("GERCHAIN_RELEASED", "independent-escrow"),
        ]

        idem = connection.execute(text(
            "SELECT key, state FROM gerchain_idempotency_records ORDER BY id"
        )).all()
        assert [(r[0], r[1]) for r in idem] == [
            ("ind-fund", "COMPLETED"),
            ("ind-lock", "COMPLETED"),
            ("ind-release", "COMPLETED"),
        ]

    engine.dispose()
