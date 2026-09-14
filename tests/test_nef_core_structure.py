from nef import (
    AssetIdentityEngine,
    AssetRegistryEngine,
    AssetStateEngine,
    AssetValidationEngine,
    AssetVersionEngine,
    DigitalAssetRecordEngine,
    OwnershipRightsEngine,
    EvidenceProvenanceEngine,
    RevaluationEngine,
    ValuationEngine,
    ValuationEvidenceEngine,
    VerificationEngine,
    EncumbranceEngine,
    CollateralEngine,
    AssetLifecycleEngine,
    NEFAuditEngine,
    NEFRecoveryEngine,
)


REQUIRED_NEF_ENGINES = (
    AssetRegistryEngine,
    AssetIdentityEngine,
    OwnershipRightsEngine,
    DigitalAssetRecordEngine,
    AssetStateEngine,
    AssetLifecycleEngine,
    ValuationEngine,
    ValuationEvidenceEngine,
    RevaluationEngine,
    EvidenceProvenanceEngine,
    VerificationEngine,
    AssetValidationEngine,
    AssetVersionEngine,
    EncumbranceEngine,
    CollateralEngine,
    NEFAuditEngine,
    NEFRecoveryEngine,
)


def test_nef_authoritative_asset_truth_engine_surface_is_complete():
    assert len(REQUIRED_NEF_ENGINES) == 17
    assert all(isinstance(engine, type) for engine in REQUIRED_NEF_ENGINES)


def test_nef_core_structure_does_not_include_value_flow_engines():
    names = {engine.__name__ for engine in REQUIRED_NEF_ENGINES}
    assert "MoneyEngine" not in names
    assert "LedgerEngine" not in names
    assert "SettlementEngine" not in names
    assert "ReleaseEngine" not in names
