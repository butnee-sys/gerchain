import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519
from network.audit_pipeline import UnifiedAuditPipeline

@pytest.fixture
def valid_crypto_material():
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    message = b"test_payload_1"
    signature = private_key.sign(message)
    return public_key, signature, message

# Since serialization needs to be imported:
from cryptography.hazmat.primitives import serialization

def test_pipeline_01_all_pass():
    pipeline = UnifiedAuditPipeline()
    private_key = ed25519.Ed25519PrivateKey.generate()
    pub_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    msg = b"test_payload_1"
    sig = private_key.sign(msg)

    event = {
        "public_key": pub_bytes,
        "signature": sig,
        "message": msg,
        "event_hash": "hash_001",
        "nonce": 1,
        "approvals_count": 3,
        "required_quorum": 2,
        "current_state": "PENDING",
        "next_state": "LOCKED"
    }
    assert pipeline.process_audit(event) == "PASS"

def test_pipeline_02_signature_fail():
    pipeline = UnifiedAuditPipeline()
    event = {
        "public_key": b"", # Invalid pubkey
        "signature": b"invalid",
        "message": b"test_payload_2",
        "event_hash": "hash_002",
        "nonce": 2,
        "approvals_count": 3,
        "required_quorum": 2,
        "current_state": "PENDING",
        "next_state": "LOCKED"
    }
    assert pipeline.process_audit(event) == "INCONCLUSIVE"

def test_pipeline_03_replay_fail():
    pipeline = UnifiedAuditPipeline()
    private_key = ed25519.Ed25519PrivateKey.generate()
    pub_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    msg = b"test_payload_3"
    sig = private_key.sign(msg)

    event_first = {
        "public_key": pub_bytes,
        "signature": sig,
        "message": msg,
        "event_hash": "hash_003",
        "nonce": 3,
        "approvals_count": 3,
        "required_quorum": 2,
        "current_state": "PENDING",
        "next_state": "LOCKED"
    }
    assert pipeline.process_audit(event_first) == "PASS"
    # Replay should fail
    assert pipeline.process_audit(event_first) == "REJECTED"

def test_pipeline_04_consensus_fail():
    pipeline = UnifiedAuditPipeline()
    private_key = ed25519.Ed25519PrivateKey.generate()
    pub_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    msg = b"test_payload_4"
    sig = private_key.sign(msg)

    event = {
        "public_key": pub_bytes,
        "signature": sig,
        "message": msg,
        "event_hash": "hash_004",
        "nonce": 4,
        "approvals_count": 1,
        "required_quorum": 3,
        "current_state": "PENDING",
        "next_state": "LOCKED"
    }
    assert pipeline.process_audit(event) == "REJECTED"

def test_pipeline_05_state_transition_fail():
    pipeline = UnifiedAuditPipeline()
    private_key = ed25519.Ed25519PrivateKey.generate()
    pub_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    msg = b"test_payload_5"
    sig = private_key.sign(msg)

    event = {
        "public_key": pub_bytes,
        "signature": sig,
        "message": msg,
        "event_hash": "hash_005",
        "nonce": 5,
        "approvals_count": 3,
        "required_quorum": 2,
        "current_state": "PENDING",
        "next_state": "RELEASED"
    }
    assert pipeline.process_audit(event) == "REJECTED"

def test_pipeline_06_missing_payload():
    pipeline = UnifiedAuditPipeline()
    event = {
        "public_key": b"key",
        "signature": b"sig",
        "message": None,
        "event_hash": "hash_006",
        "nonce": 6,
        "approvals_count": 3,
        "required_quorum": 2,
        "current_state": "PENDING",
        "next_state": "LOCKED"
    }
    assert pipeline.process_audit(event) == "INCONCLUSIVE"

def test_pipeline_07_missing_nonce():
    pipeline = UnifiedAuditPipeline()
    private_key = ed25519.Ed25519PrivateKey.generate()
    pub_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    msg = b"test_payload_7"
    sig = private_key.sign(msg)

    event = {
        "public_key": pub_bytes,
        "signature": sig,
        "message": msg,
        "event_hash": "hash_007",
        "nonce": None,
        "approvals_count": 3,
        "required_quorum": 2,
        "current_state": "PENDING",
        "next_state": "LOCKED"
    }
    assert pipeline.process_audit(event) == "INCONCLUSIVE"

def test_pipeline_08_missing_quorum_params():
    pipeline = UnifiedAuditPipeline()
    private_key = ed25519.Ed25519PrivateKey.generate()
    pub_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    msg = b"test_payload_8"
    sig = private_key.sign(msg)

    event = {
        "public_key": pub_bytes,
        "signature": sig,
        "message": msg,
        "event_hash": "hash_008",
        "nonce": 8,
        "approvals_count": None,
        "required_quorum": 2,
        "current_state": "PENDING",
        "next_state": "LOCKED"
    }
    assert pipeline.process_audit(event) == "INCONCLUSIVE"

def test_pipeline_09_unknown_states():
    pipeline = UnifiedAuditPipeline()
    private_key = ed25519.Ed25519PrivateKey.generate()
    pub_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    msg = b"test_payload_9"
    sig = private_key.sign(msg)

    event = {
        "public_key": pub_bytes,
        "signature": sig,
        "message": msg,
        "event_hash": "hash_009",
        "nonce": 9,
        "approvals_count": 3,
        "required_quorum": 2,
        "current_state": "PENDING",
        "next_state": "UNKNOWN"
    }
    assert pipeline.process_audit(event) == "INCONCLUSIVE"

def test_pipeline_10_full_lifecycle_sequence():
    pipeline = UnifiedAuditPipeline()
    private_key = ed25519.Ed25519PrivateKey.generate()
    pub_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    msg1 = b"lifecycle_1"
    sig1 = private_key.sign(msg1)
    event_lock = {
        "public_key": pub_bytes,
        "signature": sig1,
        "message": msg1,
        "event_hash": "hash_life_1",
        "nonce": 101,
        "approvals_count": 3,
        "required_quorum": 2,
        "current_state": "PENDING",
        "next_state": "LOCKED"
    }
    assert pipeline.process_audit(event_lock) == "PASS"

    msg2 = b"lifecycle_2"
    sig2 = private_key.sign(msg2)
    event_release = {
        "public_key": pub_bytes,
        "signature": sig2,
        "message": msg2,
        "event_hash": "hash_life_2",
        "nonce": 102,
        "approvals_count": 3,
        "required_quorum": 2,
        "current_state": "LOCKED",
        "next_state": "RELEASED"
    }
    assert pipeline.process_audit(event_release) == "PASS"