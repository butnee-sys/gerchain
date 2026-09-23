from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_factory_boots_against_postgresql():
    database_url = os.environ["GERCHAIN_TEST_DATABASE_URL"]
    engine = create_engine(database_url, pool_pre_ping=True)

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="pg-boot-escrow",
            amount=100,
            currency="MNT",
            witness_id="pg-boot-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    Session = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    with Session() as session:
        session.add_all(
            [
                LedgerAccountModel(
                    account_id="PG-SRC",
                    currency="MNT",
                    balance=1000,
                    version=0,
                    updated_at=now,
                ),
                LedgerAccountModel(
                    account_id="pg-boot-escrow",
                    currency="MNT",
                    balance=0,
                    version=0,
                    updated_at=now,
                ),
            ]
        )
        session.add(
            CanonicalEscrow(
                id="pg-boot-escrow",
                sender_address="PG-SRC",
                receiver_address="PG-DST",
                refund_destination="PG-SRC",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="production boot proof",
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

    engine.dispose()
