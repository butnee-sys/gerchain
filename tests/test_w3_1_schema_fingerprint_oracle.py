"""W3.1 independent logical-schema oracle contract tests."""

import importlib.util
import subprocess
import sys
from pathlib import Path

_MODULE_PATH = Path(__file__).parent / "independent" / "w3_1_schema_fingerprint_oracle.py"
_SPEC = importlib.util.spec_from_file_location("w31_oracle", _MODULE_PATH)
assert _SPEC and _SPEC.loader
_ORACLE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _ORACLE
_SPEC.loader.exec_module(_ORACLE)


def test_a_to_g_vector_suite_is_satisfied():
    result = _ORACLE.run_vector_suite()
    assert result["semantic_sensitive"] is True
    assert result["ordering_invariant"] is True
    assert result["scope_isolated"] is True


def test_h_recorded_hash_mismatch_is_not_green():
    assert _ORACLE.run_vector_suite()["wrong_hash_reconcile"] == "RECORDED_MISMATCH"


def test_i_version_mismatch_is_distinct():
    assert _ORACLE.run_vector_suite()["wrong_version_reconcile"] == "VERSION_MISMATCH"


def test_j_descriptor_version_mismatch_is_distinct():
    assert _ORACLE.run_vector_suite()["wrong_descriptor_version_reconcile"] == "DESCRIPTOR_VERSION_MISMATCH"


def test_k_fingerprint_is_deterministic():
    baseline = _ORACLE._baseline()
    assert _ORACLE.fingerprint(baseline) == _ORACLE.fingerprint(baseline)


def test_k_fresh_process_replay_is_deterministic():
    outputs = []
    for _ in range(3):
        completed = subprocess.run(
            [sys.executable, str(_MODULE_PATH)],
            check=True,
            capture_output=True,
            text=True,
        )
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        outputs.append(lines[-1])
    assert outputs[0] == outputs[1] == outputs[2]


def test_authority_metadata_does_not_change_physical_fingerprint():
    baseline = _ORACLE._baseline()
    changed_identity = _ORACLE.Descriptor(
        baseline.descriptor_version, "OTHER", baseline.tables, baseline.indexes
    )
    changed_descriptor_version = _ORACLE.Descriptor(
        "other-descriptor", baseline.schema_id, baseline.tables, baseline.indexes
    )
    assert _ORACLE.fingerprint(baseline) == _ORACLE.fingerprint(changed_identity)
    assert _ORACLE.fingerprint(baseline) == _ORACLE.fingerprint(changed_descriptor_version)


def test_backing_constraint_index_is_excluded():
    baseline = _ORACLE._baseline()
    standalone = _ORACLE.Index(
        "core", "accounts_owner_idx", ("core", "accounts"), False,
        "btree", ("owner_id",),
    )
    backing = _ORACLE.Index(
        "core", "accounts_pkey", ("core", "accounts"), True,
        "btree", ("id",), backing_constraint=True,
    )
    with_standalone = _ORACLE.Descriptor(
        baseline.descriptor_version, baseline.schema_id, baseline.tables, (standalone,)
    )
    with_backing = _ORACLE.Descriptor(
        baseline.descriptor_version, baseline.schema_id, baseline.tables, (backing,)
    )
    assert _ORACLE.fingerprint(with_backing) == _ORACLE.fingerprint(baseline)
    assert _ORACLE.fingerprint(with_standalone) != _ORACLE.fingerprint(baseline)


def test_reconcile_requires_hash_and_authority_identity():
    baseline = _ORACLE._baseline()
    value = _ORACLE.fingerprint(baseline)
    assert _ORACLE.reconcile("CORE", 1, baseline.descriptor_version, value, baseline, 1) == "MATCH"
    assert _ORACLE.reconcile("OTHER", 1, baseline.descriptor_version, value, baseline, 1) == "IDENTITY_MISMATCH"
