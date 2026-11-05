from __future__ import annotations

import os
import pytest
from sqlalchemy import create_engine, text

from persistence.atomic_release import initialize_atomic_release_schema
from persistence.idempotency_store import IdempotencyBase
from persistence.durable_idempotency import IdempotencyBase as DurableIdempotencyBase
from persistence.atomic_ledger import AtomicLedgerBase
from persistence.atomic_value_transaction import TransactionWitness
from persistence.escrow_aggregate import EscrowBase
from persistence.recovery_outbox import OutboxBase
from persistence.recovery_outbox import initialize_outbox_schema


@pytest.fixture(autouse=True)
def isolate_postgresql_core_state():
    """Keep PostgreSQL integration tests independent on the shared CI database.

    This is test-only isolation. Production state is never reset by this fixture.
    """
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url or not url.startswith("postgresql"):
        yield
        return

    engine = create_engine(url, pool_pre_ping=True)
    # Legacy test fixtures remain available for legacy compatibility tests.
    initialize_atomic_release_schema(engine)
    IdempotencyBase.metadata.create_all(engine)
    initialize_outbox_schema(engine)
    # Ensure every canonical table exists before isolation truncation.
    for base in (AtomicLedgerBase, EscrowBase, OutboxBase, DurableIdempotencyBase, TransactionWitness):
        base.metadata.create_all(engine)
    # Canonical durable idempotency is production-owned by the migration chain;
    # create_all is only a test-fixture safety net for mixed legacy/core suites.
    DurableIdempotencyBase.metadata.create_all(engine)
    # Ensure the canonical table is visible on the exact connection used by
    # the isolation boundary before issuing TRUNCATE statements.
    with engine.begin() as connection:
        DurableIdempotencyBase.metadata.create_all(connection)
    tables = (
        "gerchain_transaction_witnesses",
        "gerchain_outbox_events",
        "gerchain_idempotency_records",
        "gerchain_ledger_movements",
        "gerchain_ledger_accounts",
        "escrows",
        "gerchain_release_witnesses",
        "gerchain_release_operations",
        "gerchain_release_escrows",
        "gerchain_release_accounts",
    )
    with engine.begin() as connection:
        authorization_table_exists = connection.execute(
            text("SELECT to_regclass('gerchain_authorization_changes')")
        ).scalar_one()
        truncate_tables = tables + (
            ("gerchain_authorization_changes",) if authorization_table_exists else ()
        )
        connection.execute(
            text("TRUNCATE TABLE " + ", ".join(truncate_tables) + " RESTART IDENTITY CASCADE")
        )
    yield
    engine.dispose()


@pytest.fixture
def canonical_postgresql_engine():
    """Provide a real PostgreSQL engine when production re-performance is enabled."""
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url or not url.startswith("postgresql"):
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is not configured")
    engine = create_engine(url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture
def signed_change_factory(monkeypatch):
    """Create deterministic Ed25519 approvals for canonical PostgreSQL tests."""
    import base64
    import json

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    from dee_security.root_of_trust import RootOfTrust, SignedChange
    from persistence.signed_change_authorization import (
        canonical_payload_hash,
        canonical_refund_payload,
        canonical_release_payload,
    )

    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    owner_id = "gerchain-postgres-regression-owner"
    public_key_b64 = base64.b64encode(public_key).decode("ascii")
    monkeypatch.setenv("GERCHAIN_AUTH_OWNER_ID", owner_id)
    monkeypatch.setenv("GERCHAIN_AUTH_PUBLIC_KEY_B64", public_key_b64)
    root = RootOfTrust(owner_id=owner_id, public_key_b64=public_key_b64)

    def build(
        *,
        operation,
        transaction_id,
        escrow_id,
        destination,
        amount,
        currency,
        evidence=None,
    ):
        if operation == "RELEASE":
            protected = canonical_release_payload(
                transaction_id=transaction_id,
                escrow_id=escrow_id,
                source=escrow_id,
                destination=destination,
                amount=amount,
                currency=currency,
                decision_status="APPROVE",
                trust=True,
                transparency=True,
                performance=True,
                evidence_verified=True,
                evidence=evidence,
            )
        elif operation == "REFUND":
            protected = canonical_refund_payload(
                transaction_id=transaction_id,
                escrow_id=escrow_id,
                source=escrow_id,
                destination=destination,
                amount=amount,
                currency=currency,
                authorized=True,
                transparency=True,
                dispute_or_cancellation_verified=True,
                evidence=evidence,
            )
        else:
            raise ValueError(f"unsupported signed test operation: {operation}")

        unsigned = SignedChange(
            owner_id=owner_id,
            change_id=f"CHANGE-{transaction_id}",
            version=1,
            payload_hash=canonical_payload_hash(protected),
            signature="",
        )
        signing_bytes = json.dumps(
            unsigned.signing_payload(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        signed = SignedChange(
            owner_id=owner_id,
            change_id=unsigned.change_id,
            version=1,
            payload_hash=unsigned.payload_hash,
            signature=base64.b64encode(private_key.sign(signing_bytes)).decode("ascii"),
        )
        return root, signed, owner_id

    return build
