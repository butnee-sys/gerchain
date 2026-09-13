from __future__ import annotations

import base64
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dee_security.evidence_governance import ProtectedEvidence
from dee_security.exim_port_security import (
    EXIMPortRequest,
    EXIMPortSecurityError,
    authorize_exim_port_request,
)
from dee_security.root_of_trust import RootOfTrust


def _root() -> RootOfTrust:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    return RootOfTrust("owner-1", base64.b64encode(public).decode())


def _request(root: RootOfTrust, payload: dict) -> EXIMPortRequest:
    return EXIMPortRequest(
        request_id="REQ-EXIM-1",
        actor_id=root.owner_id,
        operation="protected-core-operation",
        contract_id="CONTRACT-1",
        evidence=ProtectedEvidence.capture(
            evidence_id="E-1", case_id="C-1", evidence=payload, root=root
        ),
    )


def test_exim_port_accepts_governed_request() -> None:
    root = _root()
    payload = {"case_id": "C-1", "verified": True}
    authorize_exim_port_request(
        root=root,
        request=_request(root, payload),
        evidence_payload=payload,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )


def test_exim_port_rejects_tampered_evidence() -> None:
    root = _root()
    payload = {"case_id": "C-1", "verified": True}
    with pytest.raises(EXIMPortSecurityError):
        authorize_exim_port_request(
            root=root,
            request=_request(root, payload),
            evidence_payload={"case_id": "C-1", "verified": False},
            trinity_proof={"trust": True, "transparency": True, "performance": True},
        )


def test_exim_port_rejects_missing_trinity() -> None:
    root = _root()
    payload = {"case_id": "C-1"}
    with pytest.raises(Exception):
        authorize_exim_port_request(
            root=root,
            request=_request(root, payload),
            evidence_payload=payload,
            trinity_proof={"trust": True, "transparency": True},
        )
