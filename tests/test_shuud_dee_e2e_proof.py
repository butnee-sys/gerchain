from __future__ import annotations

import base64
import hashlib

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security import AuthorizationPolicy, RootOfTrust
from dee_security.manifest import build_manifest
from dee_security.signing import sign_release
from nef_gerchain_port import (
    EscrowRequest,
    ExternalPortExport,
    ExternalPortImport,
    PaymentRequest,
)
from shuud.evidence import create_evidence_envelope
from shuud.incident import create_incident
from shuud.policy import GateStatus, PolicyInput
from shuud.shiid import Decision, decide
from shuud.verify import verify_incident
from shuud.witness import (
    record_evidence_locked,
    record_release_authorized,
    record_shiid_decision,
)


AMOUNT_MNT = 2_000_000


def _root_and_release():
    private = Ed25519PrivateKey.generate()
    root = RootOfTrust(
        "owner:shuud",
        base64.b64encode(private.public_key().public_bytes_raw()).decode("ascii"),
    )
    manifest = build_manifest(
        version=1,
        commit_sha="shuud-dee-e2e-proof",
        protected_paths=["shuud", "nef_gerchain_port", "dee_security"],
        artifact_hashes={"shuud": hashlib.sha256(b"shuud-e2e").hexdigest()},
        schema_version="1",
    )
    release = sign_release(
        private,
        owner_id=root.owner_id,
        release_id="SHUUD-RELEASE-001",
        commit_sha=manifest["commit_sha"],
        manifest_hash=manifest["manifest_hash"],
    )
    return root, manifest, release


def test_shuud_dee_end_to_end_proves_trust_transparency_performance():
    port = ExternalPortImport()
    export = ExternalPortExport()
    incident = create_incident(
        "Ulaanbaatar",
        vehicle_a="1234ABC",
        vehicle_b="5678DEF",
    )

    # TRUST: identity/evidence/verification/witness.
    witness = port.create_witness_chain(
        initial_state={"incident_id": incident.incident_id},
        manifest={"purpose": "SHUUD DEE proof", "application": "SHUUD"},
        witness_id="WITNESS-SHUUD-DEE-001",
    )
    evidence = create_evidence_envelope(
        incident.incident_id,
        evidence_refs=["PHOTO-001", "VIDEO-001"],
        gps_coordinates="47.9184,106.9177",
        captured_at="2026-09-13T00:00:15+00:00",
        vehicle_identity_refs=["VIN-A", "VIN-B"],
        consent_refs=["CONSENT-A", "CONSENT-B"],
        media_complete=True,
    )
    record_evidence_locked(
        witness,
        evidence,
        timestamp="2026-09-13T00:00:16+00:00",
    )

    verification = verify_incident(incident, evidence.evidence_refs)
    policy = PolicyInput(
        two_party_consent=GateStatus.PASS,
        vehicle_identity_verified=GateStatus.PASS,
        timestamp_location_verified=GateStatus.PASS,
        media_complete=GateStatus.PASS,
        no_injury=GateStatus.PASS,
        no_third_party_property_damage=GateStatus.PASS,
        damage_estimate_mnt=AMOUNT_MNT,
        dispute_present=GateStatus.PASS,
        fraud_flag=GateStatus.PASS,
        insurance_valid=GateStatus.PASS,
        beneficiary_valid=GateStatus.PASS,
        witness_verified=GateStatus.PASS,
    )
    decision = decide(incident, verification, policy=policy)
    assert decision.decision is Decision.APPROVE
    assert decision.damage_estimate_mnt == AMOUNT_MNT
    record_shiid_decision(
        witness,
        decision,
        timestamp="2026-09-13T00:00:30+00:00",
    )

    escrow = port.create_escrow(
        EscrowRequest(
            escrow_id="SHUUD-ESCROW-DEE-001",
            amount=AMOUNT_MNT,
            currency="MNT",
            settlement_provider="NEF",
            release_condition="VERIFIED_PERFORMANCE",
        ),
        witness,
    )
    escrow.transition(
        "FUNDED",
        "2026-09-13T00:00:40+00:00",
        {"incident_id": incident.incident_id},
    )
    escrow.transition(
        "LOCKED",
        "2026-09-13T00:00:45+00:00",
        {"incident_id": incident.incident_id, "condition": "VERIFIED_PERFORMANCE"},
    )

    # PERFORMANCE: the SHUUD application decision is bound to the DEE escrow.
    authorization_hash = hashlib.sha256(
        f"{incident.incident_id}:SHUUD-ESCROW-DEE-001:{AMOUNT_MNT}".encode()
    ).hexdigest()
    record_release_authorized(
        witness,
        type(
            "ReleaseGate",
            (),
            {
                "incident_id": incident.incident_id,
                "escrow_id": "SHUUD-ESCROW-DEE-001",
                "rule_version": "SHUUD-1.0",
                "authorization_hash": authorization_hash,
            },
        )(),
        timestamp="2026-09-13T00:00:55+00:00",
    )

    root, manifest, release = _root_and_release()
    port.release_escrow_authorized(
        escrow,
        incident_id=incident.incident_id,
        authorization_hash=authorization_hash,
        rule_version="SHUUD-1.0",
        timestamp="2026-09-13T00:01:00+00:00",
        root=root,
        policy=AuthorizationPolicy(),
        release=release,
        manifest=manifest,
    )

    payment = port.create_payment(
        PaymentRequest(
            escrow_id="SHUUD-ESCROW-DEE-001",
            amount=AMOUNT_MNT,
            currency="MNT",
            settlement_provider="NEF",
            evidence={"incident_id": incident.incident_id},
        )
    )
    settlement = export.settlement_status(escrow)
    witness_status = export.witness_status(witness)
    audit = export.audit_event(
        reference_id=incident.incident_id,
        event_type="SHUUD_DEE_SETTLEMENT",
        timestamp="2026-09-13T00:01:01+00:00",
        evidence_hash=evidence.content_hash,
        data={"escrow_id": settlement.escrow_id, "amount_mnt": payment.amount},
    )

    # TRUST
    assert evidence.content_hash
    assert verification.verified is True
    assert witness.entries
    assert witness.entries[0].record.event_type == "SHUUD_EVIDENCE_LOCKED"

    # TRANSPARENCY
    assert all(entry.record.event_type for entry in witness.entries)
    assert all(entry.record.event_hash for entry in witness.entries)
    assert witness_status.reference_id == witness.witness_id
    assert audit.evidence_hash == evidence.content_hash

    # PERFORMANCE
    assert escrow.get_state()["state"] == "RELEASED"
    assert settlement.status == "RELEASED"
    assert settlement.amount == AMOUNT_MNT
    assert settlement.currency == "MNT"
    assert settlement.settlement_provider == "NEF"
    assert payment.amount == AMOUNT_MNT
    assert len(witness.entries) == 6
    assert [entry.record.event_type for entry in witness.entries] == [
        "SHUUD_EVIDENCE_LOCKED",
        "SHIID_DECISION",
        "SHUUD_RELEASE_AUTHORIZED",
        "ESCROW_TRANSITION",
        "ESCROW_TRANSITION",
        "ESCROW_TRANSITION",
    ]
