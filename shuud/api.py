"""SHUUD API application-layer orchestration.

This module deliberately does not implement escrow or a second witness engine.
It exposes incident/evidence/decision data for the next integration stage.

The current registry is an in-memory sandbox adapter. Production must replace
it with durable persistence while preserving the same domain invariants.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .evidence import EvidenceEnvelope, create_evidence_envelope
from .incident import Incident, create_incident
from .metrics import measure_clearance
from .policy import GateStatus, PolicyInput
from .shiid import Decision, decide
from .verify import verify_incident

router = APIRouter(prefix="/api/v1/shuud", tags=["SHUUD"])

# Sandbox-only lifecycle registry. This prevents the API from reconstructing
# fake incidents between requests and makes resource ownership explicit.
_INCIDENTS: dict[str, Incident] = {}
_EVIDENCE: dict[str, EvidenceEnvelope] = {}


class IncidentRequest(BaseModel):
    location: str
    vehicle_a: str | None = None
    vehicle_b: str | None = None
    description: str | None = None


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
    damage_estimate_nef: float
    # Fail closed: callers must explicitly provide every policy gate.
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


class ClearanceRequest(BaseModel):
    incident_id: str
    incident_time: datetime
    clearance_time: datetime


def _get_incident(incident_id: str) -> Incident:
    incident = _INCIDENTS.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="INCIDENT_NOT_FOUND")
    return incident


def _get_evidence(incident_id: str) -> EvidenceEnvelope:
    evidence = _EVIDENCE.get(incident_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="EVIDENCE_NOT_FOUND")
    return evidence


@router.post("/incidents", response_model=dict)
def create_shuud_incident(payload: IncidentRequest):
    incident = create_incident(
        payload.location,
        vehicle_a=payload.vehicle_a,
        vehicle_b=payload.vehicle_b,
        description=payload.description,
    )
    _INCIDENTS[incident.incident_id] = incident
    return {
        "status": "success",
        "incident_id": incident.incident_id,
        "occurred_at": incident.occurred_at,
        "state": "INCIDENT_CREATED",
    }


@router.post("/evidence", response_model=dict)
def lock_shuud_evidence(payload: EvidenceRequest):
    _get_incident(payload.incident_id)
    envelope = create_evidence_envelope(
        payload.incident_id,
        evidence_refs=payload.evidence_refs,
        gps_coordinates=payload.gps_coordinates,
        captured_at=payload.captured_at,
        vehicle_identity_refs=payload.vehicle_identity_refs,
        consent_refs=payload.consent_refs,
        media_complete=payload.media_complete,
    )
    _EVIDENCE[payload.incident_id] = envelope
    return {
        "status": "success",
        "incident_id": envelope.incident_id,
        "content_hash": envelope.content_hash,
        "state": "EVIDENCE_LOCKED",
    }


@router.post("/decisions", response_model=dict)
def make_shiid_decision(payload: DecisionRequest):
    incident = _get_incident(payload.incident_id)
    evidence = _get_evidence(payload.incident_id)

    requested_refs = tuple(str(value).strip() for value in payload.evidence_refs)
    if requested_refs != evidence.evidence_refs:
        raise HTTPException(status_code=409, detail="EVIDENCE_REFERENCE_MISMATCH")

    verification = verify_incident(incident, evidence.evidence_refs)
    policy = PolicyInput(
        two_party_consent=payload.two_party_consent,
        vehicle_identity_verified=payload.vehicle_identity_verified,
        timestamp_location_verified=payload.timestamp_location_verified,
        media_complete=payload.media_complete,
        no_injury=payload.no_injury,
        no_third_party_property_damage=payload.no_third_party_property_damage,
        damage_estimate_nef=payload.damage_estimate_nef,
        dispute_present=payload.dispute_present,
        fraud_flag=payload.fraud_flag,
        insurance_valid=payload.insurance_valid,
        beneficiary_valid=payload.beneficiary_valid,
        witness_verified=payload.witness_verified,
    )
    decision = decide(incident, verification, policy=policy)
    return {
        "status": "success",
        "incident_id": decision.incident_id,
        "decision": decision.decision.value,
        "rule_version": decision.rule_version,
        "reasons": decision.reasons,
        "release_authorized": decision.decision is Decision.APPROVE,
    }


@router.post("/metrics/clearance", response_model=dict)
def calculate_clearance(payload: ClearanceRequest):
    _get_incident(payload.incident_id)
    metric = measure_clearance(
        payload.incident_id,
        payload.incident_time,
        payload.clearance_time,
    )
    return {
        "status": "success",
        "incident_id": metric.incident_id,
        "elapsed_seconds": metric.elapsed_seconds,
        "within_two_minutes": metric.within_two_minutes,
    }


__all__ = ["router"]
