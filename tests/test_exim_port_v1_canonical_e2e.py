from __future__ import annotations

import base64
from datetime import datetime

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security import AuthorizationPolicy, RootOfTrust
from dee_security.manifest import build_manifest
from dee_security.signing import sign_release
from nef_gerchain_port import EscrowRequest, ExternalPortExport, ExternalPortImport
from shuud.evidence import create_evidence_envelope
from shuud.incident import create_incident
from shuud.policy import GateStatus, PolicyInput
from shuud.release import authorize_release
from shuud.shiid import Decision, decide
from shuud.verify import verify_incident
from shuud.witness import (
    record_evidence_locked,
    record_release_authorized,
    record_shiid_decision,
)

AMOUNT_MNT = 1_250_000


def _root(private_key: Ed25519PrivateKey) -> RootOfTrust:
    return RootOfTrust(
        "owner:shuud",
        base64.b64encode(private_key.public_key().public_bytes_raw()).decode(),
    )


def _policy() -> PolicyInput:
    return PolicyInput(
        two_party_consent=GateStatus.PASS,
        vehicle_identity_verified=GateStatus.PASS,
        timestamp_location_verified=GateStatus.PASS,
        media_complete=GateStatus.PASS,
        no_injury=GateStatus.PASS,
        no_third_party_property_damage=GateStatus.PASS,
        damage_estimate_mnt=float(AMOUNT_MNT),
        dispute_present=GateStatus.PASS,
        fraud_flag=GateStatus.PASS,
        insurance_valid=GateStatus.PASS,
        beneficiary_valid=GateStatus.PASS,
        witness_verified=GateStatus.PASS,
    )


def test_canonical_exim_port_e2e_executes_dee_trinity() -> None:
    """One Port flow proves TRUST, TRANSPARENCY and PERFORMANCE together."""
    incident = create_incident(
        "Ulaanbaatar, Peace Avenue",
        vehicle_a="UBX-E2E-A",
        vehicle_b="UBX-E2E-B",
        description="minor road incident",
        occurred_at=datetime.fromisoformat("2026-09-13T16:00:00+00:00"),
    )
    evidence = create_evidence_envelope(
        incident.incident_id,
        evidence_refs=["MEDIA-E2E", "GPS-E2E"],
        gps_coordinates="47.9184,106.9177",
        captured_at="2026-09-13T16:00:05Z",
        vehicle_identity_refs=["VEH-A", "VEH-B"],
        consent_refs=["CONSENT-A", "CONSENT-B"],
        media_complete=True,
    )

    verification = verify_incident(incident, evidence.evidence_refs)
    decision = decide(incident, verification, policy=_policy(), rule_version="SHIID-1.0")
    assert verification.verified is True
    assert decision.decision is Decision.APPROVE

    # TRUST: identity/evidence/verification/witness enter through the Port.
    port = ExternalPortImport()
    export = ExternalPortExport()
    witness = port.create_witness_chain(
        initial_state={"case_id": incident.incident_id},
        manifest={"purpose": "SHUUD-DEE-PORT-E2E", "application": "SHUUD"},
        witness_id="WITNESS-SHUUD-PORT-E2E-001",
    )
    record_evidence_locked(witness, evidence, timestamp="2026-09-13T16:00:06Z")
    record_shiid_decision(witness, decision, timestamp="2026-09-13T16:00:07Z")

    evidence_out = export.evidence_status(
        evidence_id=evidence.evidence_id,
        case_id=incident.incident_id,
        evidence_hash=evidence.content_hash,
        status="VERIFIED",
        data={"source": "SHUUD", "verified": verification.verified},
    )
    assert evidence_out.evidence_hash == evidence.content_hash
    assert evidence_out.status == "VERIFIED"

    # PERFORMANCE: condition/verification → escrow → locked → authorized release.
    escrow = port.create_escrow(
        EscrowRequest(
            escrow_id="ESCROW-SHUUD-PORT-E2E-001",
            amount=AMOUNT_MNT,
            currency="MNT",
            settlement_provider="NEF",
        ),
        witness,
    )
    escrow.transition("FUNDED", "2026-09-13T16:00:08Z", {"incident_id": incident.incident_id})
    escrow.transition("LOCKED", "2026-09-13T16:00:09Z", {"incident_id": incident.incident_id})
    assert escrow.get_state()["state"] == "LOCKED"

    authorization = authorize_release(decision, escrow_id="ESCROW-SHUUD-PORT-E2E-001")
    record_release_authorized(witness, authorization, timestamp="2026-09-13T16:00:10Z")

    private = Ed25519PrivateKey.generate()
    root = _root(private)
    manifest = build_manifest(
        version=1,
        commit_sha="exim-port-v1-canonical-e2e",
        protected_paths=[
            "nef_gerchain_port/contract.py",
            "nef_gerchain_port/import_api.py",
            "nef_gerchain_port/export_api.py",
        ],
        artifact_hashes={"SHUUD": evidence.content_hash},
        schema_version="1",
    )
    release = sign_release(
        private,
        owner_id=root.owner_id,
        release_id="RELEASE-SHUUD-PORT-E2E-001",
        commit_sha=manifest["commit_sha"],
        manifest_hash=manifest["manifest_hash"],
    )

    port.release_escrow_authorized(
        escrow,
        incident_id=incident.incident_id,
        authorization_hash=authorization.authorization_hash,
        rule_version=authorization.rule_version,
        timestamp="2026-09-13T16:00:11Z",
        root=root,
        policy=AuthorizationPolicy(),
        release=release,
        manifest=manifest,
        evidence={
            "incident_id": incident.incident_id,
            "authorization_hash": authorization.authorization_hash,
        },
    )

    # TRANSPARENCY: event → evidence hash → audit → traceable settlement.
    status = export.escrow_status(escrow)
    settlement = export.settlement_status(escrow)
    witness_status = export.witness_status(witness)
    audit = export.audit_event(
        reference_id=incident.incident_id,
        event_type="SHUUD_DEE_PORT_E2E_RELEASED",
        timestamp="2026-09-13T16:00:11Z",
        evidence_hash=evidence.content_hash,
        data={"escrow_id": "ESCROW-SHUUD-PORT-E2E-001"},
    )

    assert status.status == "RELEASED"
    assert settlement.amount == AMOUNT_MNT
    assert settlement.currency == "MNT"
    assert settlement.status == "RELEASED"
    assert witness_status.status == "ACTIVE"
    assert witness_status.data["entry_count"] >= 4
    assert audit.evidence_hash == evidence.content_hash
    assert audit.data["escrow_id"] == "ESCROW-SHUUD-PORT-E2E-001"
