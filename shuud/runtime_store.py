"""SHUUD runtime state store.

Keeps persistence concerns outside the FastAPI route functions while preserving
NEF–GerChain WitnessChain and EscrowEngine as authoritative infrastructure,
accessed through the injected SHUUD application boundary.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from application_adapters import SHUUDApplicationAdapter
from .evidence import EvidenceEnvelope
from .incident import Incident
from .metrics import OperationalTiming
from .persistence import SHUUDPersistence
from .release import ReleaseAuthorization
from .shiid import Decision, SHIIDDecision


class SHUUDRuntimeStore:
    def __init__(self, persistence: SHUUDPersistence, *, app_adapter: SHUUDApplicationAdapter) -> None:
        self.persistence = persistence
        self._app_adapter = app_adapter

    @staticmethod
    def witness_bundle(witness: Any) -> dict[str, Any]:
        return {
            "manifest": witness.manifest,
            "manifest_hash": witness.manifest_hash,
            "witness_id": witness.witness_id,
            "initial_state": witness.initial_state,
            "entries": [
                {
                    "record": entry.record.__dict__,
                    "event_payload": entry.event_payload,
                    "evidence": entry.evidence,
                }
                for entry in witness.entries
            ],
        }

    def snapshot(self, *, incident: Incident, witness: Any, evidence: EvidenceEnvelope | None = None, decision: SHIIDDecision | None = None, authorization: ReleaseAuthorization | None = None, escrow: Any | None = None, settlement_provider: str = "NEF", operational_timing: OperationalTiming | None = None) -> dict[str, Any]:
        return {
            "incident": {"incident_id": incident.incident_id, "occurred_at": incident.occurred_at.isoformat(), "location": incident.location, "vehicle_a": incident.vehicle_a, "vehicle_b": incident.vehicle_b, "description": incident.description},
            "evidence": None if evidence is None else {"incident_id": evidence.incident_id, "evidence_refs": list(evidence.evidence_refs), "gps_coordinates": evidence.gps_coordinates, "captured_at": evidence.captured_at, "vehicle_identity_refs": list(evidence.vehicle_identity_refs), "consent_refs": list(evidence.consent_refs), "media_complete": evidence.media_complete, "content_hash": evidence.content_hash},
            "decision": None if decision is None else {"incident_id": decision.incident_id, "decision": decision.decision.value, "rule_version": decision.rule_version, "reasons": list(decision.reasons), "damage_estimate_mnt": decision.damage_estimate_mnt},
            "authorization": None if authorization is None else {"incident_id": authorization.incident_id, "escrow_id": authorization.escrow_id, "rule_version": authorization.rule_version, "authorization_hash": authorization.authorization_hash},
            "escrow": None if escrow is None else {"escrow_id": escrow.escrow_id, "amount": escrow.amount, "currency": escrow.currency, "state": escrow.get_state(), "records": [record.__dict__ for record in escrow.records], "settlement_provider": settlement_provider},
            "operational_timing": None if operational_timing is None else operational_timing.as_dict(),
            "witness_bundle": self.witness_bundle(witness),
        }

    def save(self, incident: Incident, witness: Any, **kwargs: Any) -> None:
        snapshot = self.snapshot(incident=incident, witness=witness, **kwargs)
        self.persistence.save_snapshot(incident.incident_id, snapshot)

    def recover_witness(self, incident_id: str) -> Any:
        return self.persistence.recover_witness(incident_id)

    @staticmethod
    def recover_incident(snapshot: dict[str, Any]) -> Incident:
        raw = snapshot["incident"]
        return Incident(incident_id=raw["incident_id"], occurred_at=datetime.fromisoformat(raw["occurred_at"]), location=raw["location"], vehicle_a=raw.get("vehicle_a"), vehicle_b=raw.get("vehicle_b"), description=raw.get("description"))

    @staticmethod
    def recover_operational_timing(snapshot: dict[str, Any]) -> OperationalTiming:
        return OperationalTiming.from_dict(snapshot.get("operational_timing") or {})

    @staticmethod
    def recover_evidence(snapshot: dict[str, Any]) -> EvidenceEnvelope | None:
        raw = snapshot.get("evidence")
        if raw is None:
            return None
        return EvidenceEnvelope(incident_id=raw["incident_id"], evidence_refs=tuple(raw["evidence_refs"]), gps_coordinates=raw["gps_coordinates"], captured_at=raw["captured_at"], vehicle_identity_refs=tuple(raw["vehicle_identity_refs"]), consent_refs=tuple(raw["consent_refs"]), media_complete=raw["media_complete"], content_hash=raw["content_hash"])

    @staticmethod
    def recover_decision(snapshot: dict[str, Any]) -> SHIIDDecision | None:
        raw = snapshot.get("decision")
        if raw is None:
            return None
        return SHIIDDecision(incident_id=raw["incident_id"], decision=Decision(raw["decision"]), rule_version=raw["rule_version"], reasons=tuple(raw["reasons"]), damage_estimate_mnt=raw.get("damage_estimate_mnt"))

    @staticmethod
    def recover_authorization(snapshot: dict[str, Any]) -> ReleaseAuthorization | None:
        raw = snapshot.get("authorization")
        if raw is None:
            return None
        return ReleaseAuthorization(incident_id=raw["incident_id"], escrow_id=raw["escrow_id"], rule_version=raw["rule_version"], authorization_hash=raw["authorization_hash"])

    def recover_escrow(self, snapshot: dict[str, Any], witness: Any) -> Any | None:
        raw = snapshot.get("escrow")
        if raw is None:
            return None
        return self._app_adapter.restore_escrow(escrow_id=raw["escrow_id"], amount=int(raw["amount"]), currency=raw["currency"], state=raw["state"], records=raw.get("records", []), witness_chain=witness)
