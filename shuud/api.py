"""SHUUD API application-layer orchestration.

This module deliberately does not implement escrow or a second witness engine.
The sandbox adapter wires SHUUD milestones to the stable NEF–GerChain external
port. Production must replace the in-memory registries with durable persistence
while preserving the same domain invariants.
"""

from datetime import datetime, timezone
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from nef_gerchain_port.gerchain_adapter import EscrowEngine, WitnessChain
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
from .witness import (
    record_evidence_locked,
    record_release_authorized,
    record_shiid_decision,
)

router = APIRouter(prefix="/api/v1/shuud", tags=["SHUUD"])

# Sandbox-only lifecycle registries. These make ownership explicit while the
# production persistence layer is still being designed.
_INCIDENTS: dict[str, Incident] = {}
_EVIDENCE: dict[str, EvidenceEnvelope] = {}
_DECISIONS: dict[str, SHIIDDecision] = {}
_AUTHORIZATIONS: dict[str, ReleaseAuthorization] = {}
_WITNESSES: dict[str, WitnessChain] = {}
_ESCROWS: dict[str, EscrowEngine] = {}
_PERSISTENCE = SHUUDPersistence(
    os.getenv("SHUUD_PERSISTENCE_URL", "sqlite:///./gerchain.db")
