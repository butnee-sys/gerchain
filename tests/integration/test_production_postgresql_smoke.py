from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dee_security.root_of_trust import RootOfTrust
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_postgresql_boot_and_canonical_release():
    import os

    url = os.environ["GERCHAIN_TEST_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    try:
        factory = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=url,
                escrow_id="prod-smoke-escrow",
                amount=10,
                currency="USD",
                witness_id="prod-smoke-witness",
            ),
            engine=engine,
        )
        runtime = factory.create()
        assert runtime.is_canonical_ledger_authoritative

        with sessionmaker(bind=engine, expire_on_commit=False)() as session:
            now = datetime.now(timezone.utc)
            session.add(
                CanonicalEscrow(
                    id="prod-smoke-escrow",
                    sender_address="SRC",
                    receiver_address="DST",
                    amount=10,
                    state=EscrowState.CREATED.value,
                    condition_desc="production smoke",
                    refund_destination="SRC",
                    currency="USD",
                    version=0,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.commit()

        runtime.create_account("SRC", initial_balance=100)
        runtime.create_account("prod-smoke-escrow", initial_balance=0)
        runtime.create_account("DST", initial_balance=0)

        runtime.fund("prod-fund-1", "SRC", "T1", {"kind": "smoke"})
        runtime.lock("prod-lock-1", "T2", {"kind": "smoke"})

        # A real RootOfTrust object is supplied; the runtime additionally
        # requires explicit authorization and Trinity evidence.
        root = RootOfTrust(
            "prod-owner",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        )
        runtime.release(
            transaction_id="prod-release-1",
            destination="DST",
            timestamp="T3",
            evidence={"kind": "smoke"},
            root=root,
            owner_id="prod-owner",
            authorized=True,
            evidence_verified=True,
            trinity_proof={
                "trust": True,
                "transparency": True,
                "performance": True,
            },
        )

        assert runtime.get_balance("SRC") == 90
        assert runtime.get_balance("prod-smoke-escrow") == 0
        assert runtime.get_balance("DST") == 10
        assert runtime.get_escrow_state()["state"] == EscrowState.RELEASED.value

        with sessionmaker(bind=engine, expire_on_commit=False)() as session:
            report = deep_reconcile_value_truth(session)
            assert report.matched, report.issues
    finally:
        engine.dispose()
