import pytest

from dee_security.e2e_governance import DEEE2EProof, DEEE2EProofError, require_dee_e2e_proof


class Root:
    owner_id = "OWNER"


def complete():
    return DEEE2EProof(**{name: True for name in DEEE2EProof.__dataclass_fields__})


def trinity():
    return {"trust": True, "transparency": True, "performance": True}


def test_complete_dee_e2e_proof_passes():
    require_dee_e2e_proof(root=Root(), owner_id="OWNER", proof=complete(), trinity_proof=trinity())


def test_missing_stage_fails_closed():
    values = {name: True for name in DEEE2EProof.__dataclass_fields__}
    values["audit_verified"] = False
    with pytest.raises(DEEE2EProofError):
        require_dee_e2e_proof(root=Root(), owner_id="OWNER", proof=DEEE2EProof(**values), trinity_proof=trinity())


def test_owner_mismatch_fails_closed():
    with pytest.raises(DEEE2EProofError):
        require_dee_e2e_proof(root=Root(), owner_id="APP", proof=complete(), trinity_proof=trinity())


def test_missing_trinity_fails_closed():
    with pytest.raises(DEEE2EProofError):
        require_dee_e2e_proof(root=Root(), owner_id="OWNER", proof=complete(), trinity_proof={"trust": True})
