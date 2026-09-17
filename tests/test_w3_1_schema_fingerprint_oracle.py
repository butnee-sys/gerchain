"""W3.1 independent logical-schema oracle contract tests."""

from tests.independent.w3_1_schema_fingerprint_oracle import (
    Descriptor,
    Index,
    _baseline,
    _replace_accounts,
    _type,
    fingerprint,
    reconcile,
    run_vector_suite,
)


def test_a_to_g_vector_suite_is_satisfied():
    result = run_vector_suite()
    assert result["semantic_sensitive"] is True
    assert result["ordering_invariant"] is True
    assert result["scope_isolated"] is True


def test_h_recorded_hash_mismatch_is_not_green():
    result = run_vector_suite()
    assert result["wrong_hash_reconcile"] == "RECORDED_MISMATCH"


def test_i_version_mismatch_is_distinct_from_hash_mismatch():
    result = run_vector_suite()
    assert result["wrong_version_reconcile"] == "VERSION_MISMATCH"


def test_j_descriptor_version_mismatch_is_distinct():
    result = run_vector_suite()
    assert result["wrong_descriptor_version_reconcile"] == "DESCRIPTOR_VERSION_MISMATCH"


def test_k_fingerprint_is_deterministic():
    baseline = _baseline()
    assert fingerprint(baseline) == fingerprint(baseline)


def test_authority_metadata_does_not_change_physical_fingerprint():
    baseline = _baseline()
    changed_identity = Descriptor(
        descriptor_version=baseline.descriptor_version,
        schema_id="OTHER",
        tables=baseline.tables,
        indexes=baseline.indexes,
    )
    assert fingerprint(baseline) == fingerprint(changed_identity)


def test_backing_constraint_index_is_excluded_from_physical_fingerprint():
    baseline = _baseline()
    standalone = Index(
        "core",
        "accounts_owner_idx",
        ("core", "accounts"),
        False,
        "btree",
        ("owner_id",),
    )
    backing = Index(
        "core",
        "accounts_pkey",
        ("core", "accounts"),
        True,
        "btree",
        ("id",),
        backing_constraint=True,
    )
    with_standalone = Descriptor(
        baseline.descriptor_version,
        baseline.schema_id,
        baseline.tables,
        (standalone,),
    )
    with_backing = Descriptor(
        baseline.descriptor_version,
        baseline.schema_id,
        baseline.tables,
        (backing,),
    )
    assert fingerprint(with_backing) == fingerprint(baseline)
    assert fingerprint(with_standalone) != fingerprint(baseline)


def test_reconcile_requires_hash_and_authority_identity():
    baseline = _baseline()
    value = fingerprint(baseline)
    assert reconcile("CORE", 1, baseline.descriptor_version, value, baseline, 1) == "MATCH"
    assert reconcile("OTHER", 1, baseline.descriptor_version, value, baseline, 1) == "IDENTITY_MISMATCH"
