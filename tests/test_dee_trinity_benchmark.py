from __future__ import annotations

import base64
import time
from statistics import mean

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
from shuud.witness import record_evidence_locked, record_release_authorized, record_shiid_decision

ITERATIONS = 10
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


def _run_case(index: int) -> dict[str, int]:
    case_id = f"BENCH-{index:03d}"
    escrow_id = f"ESCROW-{case_id}"
    now = time.perf_counter_ns

    t0 = now()
    incident = create_incident(
        "Ulaanbaatar, Peace Avenue",
        vehicle_a=f"UBX-A-{index:03d}",
        vehicle_b=f"UBX-B-{index:03d}",
        description="minor road incident",
        occurred_at=__import__("datetime").datetime.fromisoformat("2026-09-13T16:00:00+00:00"),
    )
    evidence = create_evidence_envelope(
        incident.incident_id,
        evidence_refs=[f"MEDIA-{index:03d}", f"GPS-{index:03d}"],
        gps_coordinates="47.9184,106.9177",
        captured_at="2026-09-13T16:00:05Z",
        vehicle_identity_refs=[f"VEH-A-{index:03d}", f"VEH-B-{index:03d}"],
        consent_refs=[f"CONSENT-A-{index:03d}", f"CONSENT-B-{index:03d}"],
        media_complete=True,
    )
    verification = verify_incident(incident, evidence.evidence_refs)
    decision = decide(incident, verification, policy=_policy(), rule_version="SHIID-1.0")
    assert verification.verified is True
    assert decision.decision is Decision.APPROVE
    t1 = now()

    port = ExternalPortImport()
    export = ExternalPortExport()
    witness = port.create_witness_chain(
        initial_state={"case_id": incident.incident_id},
        manifest={"purpose": "SHUUD-DEE-BENCHMARK", "application": "SHUUD"},
        witness_id=f"WITNESS-{case_id}",
    )
    record_evidence_locked(witness, evidence, timestamp="2026-09-13T16:00:06Z")
    record_shiid_decision(witness, decision, timestamp="2026-09-13T16:00:07Z")
    t2 = now()

    escrow = port.create_escrow(
        EscrowRequest(
            escrow_id=escrow_id,
            amount=AMOUNT_MNT,
            currency="MNT",
            settlement_provider="NEF",
        ),
        witness,
    )
    escrow.transition("FUNDED", "2026-09-13T16:00:08Z", {"incident_id": incident.incident_id})
    escrow.transition("LOCKED", "2026-09-13T16:00:09Z", {"incident_id": incident.incident_id})
    t3 = now()

    authorization = authorize_release(decision, escrow_id=escrow_id)
    record_release_authorized(witness, authorization, timestamp="2026-09-13T16:00:10Z")
    private = Ed25519PrivateKey.generate()
    root = _root(private)
    manifest = build_manifest(
        version=1,
        commit_sha="dee-trinity-benchmark",
        protected_paths=[
            "nef_gerchain_port/contract.py",
            "nef_gerchain_port/import_api.py",
        ],
        artifact_hashes={"SHUUD": evidence.content_hash},
        schema_version="1",
    )
    release = sign_release(
        private,
        owner_id=root.owner_id,
        release_id=f"RELEASE-{case_id}",
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
    t4 = now()

    status = export.escrow_status(escrow)
    settlement = export.settlement_status(escrow)
    witness_status = export.witness_status(witness)
    audit = export.audit_event(
        reference_id=incident.incident_id,
        event_type="SHUUD_DEE_BENCHMARK_RELEASED",
        timestamp="2026-09-13T16:00:11Z",
        evidence_hash=evidence.content_hash,
    )
    assert status.status == "RELEASED"
    assert settlement.amount == AMOUNT_MNT
    assert settlement.currency == "MNT"
    assert witness_status.status == "ACTIVE"
    assert witness_status.data["entry_count"] >= 4
    assert audit.evidence_hash == evidence.content_hash
    t5 = now()

    return {
        "trust_ns": t2 - t1,
        "transparency_ns": t5 - t4,
        "performance_ns": t4 - t2,
        "total_ns": t5 - t0,
    }


def test_dee_trinity_benchmark():
    samples = [_run_case(index) for index in range(1, ITERATIONS + 1)]
    totals = [sample["total_ns"] for sample in samples]

    assert len(samples) == ITERATIONS
    assert all(value > 0 for value in totals)

    summary = {
        "iterations": ITERATIONS,
        "successful": len(samples),
        "total_ms_mean": mean(totals) / 1_000_000,
        "trust_ms_mean": mean(sample["trust_ns"] for sample in samples) / 1_000_000,
        "performance_ms_mean": mean(sample["performance_ns"] for sample in samples) / 1_000_000,
        "transparency_ms_mean": mean(sample["transparency_ns"] for sample in samples) / 1_000_000,
    }
    print(f"DEE_TRINITY_BENCHMARK {summary}")
