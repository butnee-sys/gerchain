from __future__ import annotations

import os
import base64
import json
from datetime import datetime, timezone

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory
from dee_security.root_of_trust import RootOfTrust, SignedChange
from persistence.signed_change_authorization import canonical_release_payload, canonical_payload_hash


def test_production_postgresql_runtime_boot_and_canonical_value_flow(monkeypatch):
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    monkeypatch.setenv("GERCHAIN_AUTH_OWNER_ID", "ci-owner")
    monkeypatch.setenv("GERCHAIN_AUTH_PUBLIC_KEY_B64", base64.b64encode(public_key).decode("ascii"))
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=os.environ["GERCHAIN_DATABASE_URL"],
            escrow_id="ci-escrow",
            amount=100,
            currency="USD",
            witness_id="ci-witness",
        )
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    now = datetime.now(timezone.utc)
    with factory.session_factory() as session:
        from persistence.atomic_ledger import PostgreSQLAtomicLedger
        ledger = PostgreSQLAtomicLedger(factory.session_factory)
        ledger.create_account_in_transaction(session, "SRC", "USD", 100)
        ledger.create_account_in_transaction(session, "ci-escrow", "USD", 0)
        ledger.create_account_in_transaction(session, "DST", "USD", 0)
        session.add(CanonicalEscrow(
            id="ci-escrow", sender_address="SRC", receiver_address="DST",
            refund_destination="SRC", amount=100, state="CREATED",
            condition_desc="CI production gate", currency="USD", version=0,
            created_at=now, updated_at=now,
        ))
        session.commit()

    runtime.fund("ci-fund", "SRC", now.isoformat(), {"source": "ci"})
    runtime.lock("ci-lock", now.isoformat(), {"source": "ci"})
    evidence = {"source": "ci"}
    payload = canonical_release_payload(
        transaction_id="ci-release",
        escrow_id="ci-escrow",
        source="ci-escrow",
        destination="DST",
        amount=100,
        currency="USD",
        decision_status="APPROVE",
        trust=True,
        transparency=True,
        performance=True,
        evidence_verified=True,
        evidence=evidence,
    )
    unsigned = SignedChange(
        owner_id="ci-owner",
        change_id="change-ci-release",
        version=1,
        payload_hash=canonical_payload_hash(payload),
        signature="",
    )
    signed_change = SignedChange(
        owner_id=unsigned.owner_id,
        change_id=unsigned.change_id,
        version=unsigned.version,
        payload_hash=unsigned.payload_hash,
        signature=base64.b64encode(private_key.sign(json.dumps(
            unsigned.signing_payload(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8"))).decode("ascii"),
    )
    root = RootOfTrust(
        "ci-owner",
        base64.b64encode(public_key).decode("ascii"),
    )
    runtime.release(
        transaction_id="ci-release", destination="DST",
        timestamp=now.isoformat(), evidence=evidence,
        root=root, signed_change=signed_change, owner_id="ci-owner", authorized=False,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )

    assert runtime.get_balance("SRC") == 0
    assert runtime.get_balance("ci-escrow") == 0
    assert runtime.get_balance("DST") == 100
    assert runtime.get_escrow_state()["state"] == "RELEASED"

    with factory.session_factory() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    factory.engine.dispose()
