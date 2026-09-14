"""SHUUD API application-layer orchestration.

SHUUD is an external application. Core NEF–GerChain engines are accessed only
through the stable EXIM Escrow Port boundary.
"""

from datetime import datetime, timezone
import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from nef_gerchain_port import ExternalPortImport, EscrowRequest as PortEscrowRequest
from .evidence import EvidenceEnvelope, create_evidence_envelope
from .incident import Incident, create_incident
from .measurement_api import MeasurementSummaryRequest
from .measurement_summary import build_measurement_summary
from .metrics import OperationalTiming, measure_clearance
from .policy import GateStatus, PolicyInput
from .persistence import SHUUDPersistence
from .runtime_store import SHUUDRuntimeStore
from .release import ReleaseAuthorization, authorize_release, release_escrow
from .shiid import Decision, SHIIDDecision, decide
from .verify import verify_incident
from .witness import record_evidence_locked, record_release_authorized, record_shiid_decision

router = APIRouter(prefix="/api/v1/shuud", tags=["SHUUD"])

_INCIDENTS: dict[str, Incident] = {}
_EVIDENCE: dict[str, EvidenceEnvelope] = {}
_DECISIONS: dict[str, SHIIDDecision] = {}
_AUTHORIZATIONS: dict[str, ReleaseAuthorization] = {}
_WITNESSES: dict[str, Any] = {}
_ESCROWS: dict[str, Any] = {}
_PERSISTENCE = SHUUDPersistence(os.getenv("SHUUD_PERSISTENCE_URL", "sqlite:///./gerchain.db"))
_RUNTIME_STORE = SHUUDRuntimeStore(_PERSISTENCE)
_PORT_IMPORT = ExternalPortImport()


class IncidentRequest(BaseModel):
    location: str
    vehicle_a: str | None = None
    vehicle_b: str | None = None
    description: str | None = None
    occurred_at: datetime | None = None


class EvidenceRequest(BaseModel):
    incident_id: str
    evidence_refs: list[str] = Field(min_length=1)
    gps_coordinates: str
    captured_at: str
    vehicle_identity_refs: list[str] = Field(min_length=1)
    consent_refs: list[str] = Field(min_length=1)
    media_complete: bool


class DecisionRequest(BaseModel):
    incident_id: str
    evidence_refs: list[str] = Field(min_length=1)
    damage_estimate_mnt: int = Field(gt=0)
    two_party_consent: GateStatus = GateStatus.UNKNOWN
    vehicle_identity_verified: GateStatus = GateStatus.UNKNOWN
    timestamp_location_verified: GateStatus = GateStatus.UNKNOWN
    media_complete: GateStatus = GateStatus.UNKNOWN
    no_injury: GateStatus = GateStatus.UNKNOWN
    no_third_party_property_damage: GateStatus = GateStatus.UNKNOWN
    dispute_present: GateStatus = GateStatus.UNKNOWN
    fraud_flag: GateStatus = GateStatus.UNKNOWN
    insurance_valid: GateStatus = GateStatus.UNKNOWN
    beneficiary_valid: GateStatus = GateStatus.UNKNOWN
    witness_verified: GateStatus = GateStatus.UNKNOWN


class EscrowRequest(BaseModel):
    incident_id: str
    escrow_id: str
    amount_mnt: int = Field(gt=0)
    settlement_provider: str = "NEF"


class ReleaseRequest(BaseModel):
    incident_id: str
    escrow_id: str


class ClearanceRequest(BaseModel):
    incident_id: str
    clearance_time: datetime | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _timing_for_snapshot(snapshot: dict, incident: Incident) -> OperationalTiming:
    timing = _RUNTIME_STORE.recover_operational_timing(snapshot)
    if not timing.timestamps:
        timing = timing.with_milestone("incident_created_at", incident.occurred_at)
    return timing


def _timing_for_incident(incident_id: str) -> tuple[dict, Incident, OperationalTiming]:
    incident = _get_incident(incident_id)
    snapshot = _PERSISTENCE.load_snapshot(incident_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="INCIDENT_NOT_FOUND")
    return snapshot, incident, _timing_for_snapshot(snapshot, incident)


def _save_timing_snapshot(incident_id: str, snapshot: dict, timing: OperationalTiming) -> None:
    updated = dict(snapshot)
    updated["operational_timing"] = timing.as_dict()
    if not _PERSISTENCE.save_snapshot_if_current(incident_id, snapshot, updated):
        raise HTTPException(status_code=409, detail="SHUUD_STATE_CONFLICT")


def _get_incident(incident_id: str) -> Incident:
    _restore(incident_id)
    incident = _INCIDENTS.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="INCIDENT_NOT_FOUND")
    return incident


def _get_evidence(incident_id: str) -> EvidenceEnvelope:
    _restore(incident_id)
    evidence = _EVIDENCE.get(incident_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="EVIDENCE_NOT_FOUND")
    return evidence


def _restore(incident_id: str) -> None:
    if incident_id in _INCIDENTS:
        return
    snapshot = _PERSISTENCE.load_snapshot(incident_id)
    if snapshot is None:
        return
    incident = _RUNTIME_STORE.recover_incident(snapshot)
    witness = _RUNTIME_STORE.recover_witness(incident_id)
    evidence = _RUNTIME_STORE.recover_evidence(snapshot)
    decision = _RUNTIME_STORE.recover_decision(snapshot)
    authorization = _RUNTIME_STORE.recover_authorization(snapshot)
    escrow = _RUNTIME_STORE.recover_escrow(snapshot, witness)
    _INCIDENTS[incident_id] = incident
    _WITNESSES[incident_id] = witness
    if evidence is not None:
        _EVIDENCE[incident_id] = evidence
    if decision is not None:
        _DECISIONS[incident_id] = decision
    if authorization is not None:
        _AUTHORIZATIONS[incident_id] = authorization
    if escrow is not None:
        _ESCROWS[escrow.escrow_id] = escrow


def _get_witness(incident_id: str) -> Any:
    _restore(incident_id)
    witness = _WITNESSES.get(incident_id)
    if witness is None:
        raise HTTPException(status_code=404, detail="WITNESS_NOT_FOUND")
    return witness


@router.post("/incidents", response_model=dict)
def create_shuud_incident(payload: IncidentRequest):
    incident = create_incident(payload.location, vehicle_a=payload.vehicle_a, vehicle_b=payload.vehicle_b,
                               description=payload.description, occurred_at=payload.occurred_at)
    witness = _PORT_IMPORT.create_witness_chain(
        initial_state={"value": 0, "incident_id": incident.incident_id},
        manifest={"purpose": "SHUUD sandbox", "incident_id": incident.incident_id},
        witness_id="WITNESS-ROOT-001",
    )
    timing = OperationalTiming({}).with_milestone("incident_created_at", incident.occurred_at)
    _INCIDENTS[incident.incident_id] = incident
    _WITNESSES[incident.incident_id] = witness
    _RUNTIME_STORE.save(incident, witness, operational_timing=timing)
    return {"status": "success", "incident_id": incident.incident_id, "occurred_at": incident.occurred_at,
            "state": "INCIDENT_CREATED"}


@router.post("/evidence", response_model=dict)
def lock_shuud_evidence(payload: EvidenceRequest):
    incident = _get_incident(payload.incident_id)
    witness = _get_witness(payload.incident_id)
    envelope = create_evidence_envelope(payload.incident_id, evidence_refs=payload.evidence_refs,
                                         gps_coordinates=payload.gps_coordinates, captured_at=payload.captured_at,
                                         vehicle_identity_refs=payload.vehicle_identity_refs,
                                         consent_refs=payload.consent_refs, media_complete=payload.media_complete)
    record = record_evidence_locked(witness, envelope, timestamp=payload.captured_at)
    timing = _timing_for_incident(payload.incident_id)[2].with_milestone("evidence_locked_at", _now())
    _EVIDENCE[payload.incident_id] = envelope
    _RUNTIME_STORE.save(incident, witness, evidence=envelope, operational_timing=timing)
    return {"status": "success", "incident_id": envelope.incident_id, "content_hash": envelope.content_hash,
            "witness_event_id": record.event_id, "state": "EVIDENCE_LOCKED"}


@router.post("/decisions", response_model=dict)
def make_shiid_decision(payload: DecisionRequest):
    incident = _get_incident(payload.incident_id)
    evidence = _get_evidence(payload.incident_id)
    witness = _get_witness(payload.incident_id)
    requested_refs = tuple(str(value).strip() for value in payload.evidence_refs)
    if requested_refs != evidence.evidence_refs:
        raise HTTPException(status_code=409, detail="EVIDENCE_REFERENCE_MISMATCH")
    verification = verify_incident(incident, evidence.evidence_refs)
    verified_at = _now()
    policy = PolicyInput(two_party_consent=payload.two_party_consent,
                         vehicle_identity_verified=payload.vehicle_identity_verified,
                         timestamp_location_verified=payload.timestamp_location_verified,
                         media_complete=payload.media_complete, no_injury=payload.no_injury,
                         no_third_party_property_damage=payload.no_third_party_property_damage,
                         damage_estimate_mnt=payload.damage_estimate_mnt, dispute_present=payload.dispute_present,
                         fraud_flag=payload.fraud_flag, insurance_valid=payload.insurance_valid,
                         beneficiary_valid=payload.beneficiary_valid, witness_verified=payload.witness_verified)
    decision = decide(incident, verification, policy=policy)
    decided_at = _now()
    record_shiid_decision(witness, decision, timestamp=decided_at.isoformat())
    timing = _timing_for_incident(payload.incident_id)[2]
    timing = timing.with_milestone("verification_completed_at", verified_at)
    timing = timing.with_milestone("shiid_decided_at", decided_at)
    _DECISIONS[payload.incident_id] = decision
    _RUNTIME_STORE.save(incident, witness, evidence=evidence, decision=decision, operational_timing=timing)
    return {"status": "success", "incident_id": decision.incident_id, "decision": decision.decision.value,
            "rule_version": decision.rule_version, "reasons": decision.reasons,
            "release_authorized": decision.decision is Decision.APPROVE}


@router.post("/escrows", response_model=dict)
def create_shuud_escrow(payload: EscrowRequest):
    incident = _get_incident(payload.incident_id)
    if payload.escrow_id in _ESCROWS:
        raise HTTPException(status_code=409, detail="ESCROW_ALREADY_EXISTS")
    witness = _get_witness(payload.incident_id)
    escrow = _PORT_IMPORT.create_escrow(PortEscrowRequest(escrow_id=payload.escrow_id, amount=payload.amount_mnt,
                                                          currency="MNT", settlement_provider=payload.settlement_provider), witness)
    now = _now().isoformat()
    escrow.transition("FUNDED", now, {"incident_id": payload.incident_id, "source": "SHUUD_SANDBOX",
                                      "settlement_provider": payload.settlement_provider})
    escrow.transition("LOCKED", _now().isoformat(), {"incident_id": payload.incident_id, "source": "SHUUD_SANDBOX",
                                                       "settlement_provider": payload.settlement_provider})
    _ESCROWS[payload.escrow_id] = escrow
    _, _, timing = _timing_for_incident(payload.incident_id)
    _RUNTIME_STORE.save(incident, witness, evidence=_EVIDENCE.get(payload.incident_id),
                        decision=_DECISIONS.get(payload.incident_id), authorization=_AUTHORIZATIONS.get(payload.incident_id),
                        escrow=escrow, settlement_provider=payload.settlement_provider, operational_timing=timing)
    return {"status": "success", "incident_id": payload.incident_id, "escrow_id": payload.escrow_id,
            "currency": "MNT", "settlement_provider": payload.settlement_provider, "state": escrow.get_state()["state"]}


@router.post("/release", response_model=dict)
def release_shuud_escrow(payload: ReleaseRequest):
    expected_snapshot = _PERSISTENCE.load_snapshot(payload.incident_id)
    if expected_snapshot is None:
        raise HTTPException(status_code=404, detail="INCIDENT_NOT_FOUND")
    _get_incident(payload.incident_id)
    witness = _get_witness(payload.incident_id)
    decision = _DECISIONS.get(payload.incident_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="DECISION_NOT_FOUND")
    if decision.decision is not Decision.APPROVE:
        raise HTTPException(status_code=409, detail="RELEASE_NOT_AUTHORIZED")
    escrow = _ESCROWS.get(payload.escrow_id)
    if escrow is None:
        raise HTTPException(status_code=404, detail="ESCROW_NOT_FOUND")
    authorization = _AUTHORIZATIONS.get(payload.incident_id)
    if authorization is None:
        authorization = authorize_release(decision, escrow_id=payload.escrow_id)
        record_release_authorized(witness, authorization, timestamp=_now().isoformat())
        _AUTHORIZATIONS[payload.incident_id] = authorization
    release_evidence = {"incident_id": payload.incident_id, "authorization_hash": authorization.authorization_hash,
                        "rule_version": authorization.rule_version, "settlement_provider": "NEF"}
    released_at = _now()
    record = release_escrow(escrow, authorization, timestamp=released_at.isoformat(), evidence=release_evidence)
    timing = _timing_for_snapshot(expected_snapshot, _INCIDENTS[payload.incident_id]).with_milestone("settlement_released_at", released_at)
    new_snapshot = _RUNTIME_STORE.snapshot(incident=_INCIDENTS[payload.incident_id], witness=witness,
        evidence=_EVIDENCE.get(payload.incident_id), decision=decision, authorization=authorization, escrow=escrow,
        settlement_provider="NEF", operational_timing=timing)
    if not _PERSISTENCE.save_snapshot_if_current(payload.incident_id, expected_snapshot, new_snapshot):
        raise HTTPException(status_code=409, detail="SHUUD_STATE_CONFLICT")
    return {"status": "success", "incident_id": payload.incident_id, "escrow_id": payload.escrow_id,
            "authorization_hash": authorization.authorization_hash, "previous_state": record.previous_state,
            "new_state": record.new_state}


@router.post("/metrics/clearance", response_model=dict)
def calculate_clearance(payload: ClearanceRequest):
    snapshot, incident, timing = _timing_for_incident(payload.incident_id)
    clearance_time = payload.clearance_time or _now()
    updated_timing = timing.with_milestone("clearance_confirmed_at", clearance_time)
    _save_timing_snapshot(payload.incident_id, snapshot, updated_timing)
    metric = measure_clearance(payload.incident_id, incident.occurred_at, clearance_time)
    return {"status": "success", "incident_id": metric.incident_id, "elapsed_seconds": metric.elapsed_seconds,
            "within_two_minutes": metric.within_two_minutes, "milestones": updated_timing.as_dict(),
            "durations": updated_timing.durations()}


@router.get("/metrics/{incident_id}", response_model=dict)
def get_operational_metrics(incident_id: str):
    snapshot, incident, timing = _timing_for_incident(incident_id)
    durations = timing.durations()
    return {"status": "success", "incident_id": incident.incident_id, "milestones": timing.as_dict(),
            "durations": durations, "within_two_minutes": timing.within_two_minutes(), "snapshot_persisted": snapshot is not None}


@router.post("/metrics/{incident_id}/summary", response_model=dict)
def get_measurement_summary(incident_id: str, payload: MeasurementSummaryRequest):
    _, incident, timing = _timing_for_incident(incident_id)
    summary = build_measurement_summary(incident_id=incident.incident_id, timing=timing,
        baseline_seconds=payload.baseline_seconds, affected_vehicles=payload.affected_vehicles,
        vehicle_value_per_minute_mnt=payload.vehicle_value_per_minute_mnt,
        insurer_cost_per_minute_mnt=payload.insurer_cost_per_minute_mnt,
        public_road_cost_per_minute_mnt=payload.public_road_cost_per_minute_mnt)
    return {"status": "success", **summary.as_dict()}
