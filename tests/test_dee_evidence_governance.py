from __future__ import annotations

import base64
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security.evidence_governance import (
    EvidenceGovernanceError,
    ProtectedEvidence,
    evidence_hash,
    require_protected_evidence,
)
from dee_security.root_of_trust import RootOfTrust


def _root() -> RootOfTrust:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    return RootOfTrust("owner-1", base64.b64encode(public).decode())


def test_evidence_hash_is_deterministic() -> None:
    value = {"case": "C-1", "amount": 2_000_000}
    assert evidence_hash(value) == evidence_hash({"amount": 2_000_000, "case": "C-1"})


def test_evidence_requires_integrity_and_trinity() -> None:
    root = _root()
    payload = {"case": "C-1", "confirmed": True}
    evidence = ProtectedEvidence.capture(
        evidence_id="E-1", case_id="C-1", evidence=payload, root=root
    )
    require_protected_evidence(
        root=root,
        evidence=evidence,
        payload=payload,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )


def test_tampered_evidence_fails_closed() -> None:
    root = _root()
    payload = {"case": "C-1", "confirmed": True}
    evidence = ProtectedEvidence.capture(
        evidence_id="E-1", case_id="C-1", evidence=payload, root=root
    )
    with pytest.raises(EvidenceGovernanceError):
        require_protected_evidence(
            root=root,
            evidence=evidence,
            payload={"case": "C-1", "confirmed": False},
            trinity_proof={"trust": True, "transparency": True, "performance": True},
        )


def test_missing_trinity_dimension_fails_closed() -> None:
    root = _root()
    payload = {"case": "C-1"}
    evidence = ProtectedEvidence.capture(
        evidence_id="E-1", case_id="C-1", evidence=payload, root=root
    )
    with pytest.raises(Exception):
        require_protected_evidence(
            root=root,
            evidence=evidence,
            payload=payload,
            trinity_proof={"trust": True, "transparency": True},
        )
