"""SHUUD evidence envelope.

The application layer captures evidence metadata and produces a deterministic
content commitment. GerChain WitnessChain remains the authoritative recorder.
"""

from dataclasses import dataclass
from typing import Sequence

from core.hashing import domain_hash


@dataclass(frozen=True)
class EvidenceEnvelope:
    incident_id: str
    evidence_refs: tuple[str, ...]
    gps_coordinates: str
    captured_at: str
    vehicle_identity_refs: tuple[str, ...]
    consent_refs: tuple[str, ...]
    media_complete: bool
    content_hash: str


def create_evidence_envelope(
    incident_id: str,
    *,
    evidence_refs: Sequence[str],
    gps_coordinates: str,
    captured_at: str,
    vehicle_identity_refs: Sequence[str],
    consent_refs: Sequence[str],
    media_complete: bool,
) -> EvidenceEnvelope:
    if not incident_id.strip():
        raise ValueError("incident_id is required")
    if not evidence_refs:
        raise ValueError("evidence_refs are required")
    if not gps_coordinates.strip():
        raise ValueError("gps_coordinates are required")
    if not captured_at.strip():
        raise ValueError("captured_at is required")
    if not vehicle_identity_refs:
        raise ValueError("vehicle_identity_refs are required")
    if not consent_refs:
        raise ValueError("consent_refs are required")
    if not media_complete:
        raise ValueError("media evidence is incomplete")

    refs = tuple(str(value).strip() for value in evidence_refs)
    vehicle_refs = tuple(str(value).strip() for value in vehicle_identity_refs)
    consent = tuple(str(value).strip() for value in consent_refs)

    payload = {
        "incident_id": incident_id.strip(),
        "evidence_refs": list(refs),
        "gps_coordinates": gps_coordinates.strip(),
        "captured_at": captured_at.strip(),
        "vehicle_identity_refs": list(vehicle_refs),
        "consent_refs": list(consent),
        "media_complete": True,
    }

    return EvidenceEnvelope(
        incident_id=incident_id.strip(),
        evidence_refs=refs,
        gps_coordinates=gps_coordinates.strip(),
        captured_at=captured_at.strip(),
        vehicle_identity_refs=vehicle_refs,
        consent_refs=consent,
        media_complete=True,
        content_hash=domain_hash("SHUUD_EVIDENCE", payload),
    )


__all__ = ["EvidenceEnvelope", "create_evidence_envelope"]
