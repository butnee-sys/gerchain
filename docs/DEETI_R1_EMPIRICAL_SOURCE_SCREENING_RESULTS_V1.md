# DEETI R1 Empirical Source Screening Results v1

**Status:** R1 preparation
**Scientific status:** R0 — Registered hypothesis

## Purpose

Record the first external-source screening before any confirmatory outcome analysis. The purpose is to prevent source selection from being driven by favorable results.

## Candidate A — World Bank Enterprise Surveys (WBES)

**Assessment:** SECONDARY_ELIGIBLE / candidate for external-validity analysis; **not primary for the foundational ETI test at present**.

WBES provides representative firm-level observations across many economies and years, and its public metadata covers business environment, finance, infrastructure and performance. The 2023/2024 survey instruments include electronic-payment variables such as percentage of sales received electronically, days to receive payment, transaction cost, and commercial-dispute indicators.

However, WBES does not directly observe the DEETI construct `ETI = Trust + Transparency + Verified Fulfilment` at transaction-episode level. Therefore ETI cannot currently be reconstructed without introducing proxy assumptions. Using those proxies as the primary exposure would weaken construct validity and could create measurement circularity.

**Decision:** do not use as the primary confirmatory source. Use only as a secondary/external-validity source after its measurement mapping is separately validated.

## Candidate B — public blockchain escrow contracts / on-chain records

**Assessment:** EXPLORATORY_ONLY until a complete, independently reproducible transaction-level extraction is established.

Public smart-contract records can provide strong provenance for state transitions, funding, release, refund and timing. Existing public escrow contracts demonstrate that such states can be observable on-chain. However, an on-chain record alone does not establish the off-chain Trust and Verified Fulfilment components required by the frozen ETI definition. Contract selection and transaction labeling also require an auditable inclusion rule.

**Decision:** exploratory until ETI/O1 separation, population coverage, negative evidence and independent coding are established.

## Candidate C — synthetic e-commerce datasets

**Assessment:** REJECTED for confirmatory empirical inference.

Public synthetic e-commerce datasets can be useful for testing code and data transformations, but synthetic observations are not evidence about real digital-economic behavior.

**Decision:** test fixtures only.

## Candidate D — published escrow/smart-contract experimental studies with real-data-derived workloads

**Assessment:** SECONDARY_ONLY / methodological benchmark.

Recent literature reports controlled escrow experiments using real datasets as workload material. Such work can provide useful methodological benchmarks for settlement, dispute and atomicity measures, but workload generation is not equivalent to observing naturally occurring economic transactions. Therefore these studies cannot by themselves establish the DEETI foundational capability claim.

## Primary-source conclusion

At this screening stage, **no external public source has passed the full primary gate**:

```text
SourceAccessible
∧ ObservationUnitDefined
∧ O1Reconstructable
∧ ETIReconstructable
∧ ETI_O1_Separated
∧ TemporalOrderingValid
∧ ComparisonFeasible
∧ ProvenanceComplete
∧ NegativeEvidenceAvailable
∧ DefinitionStabilityVerified
∧ ReproducibilityFeasible
```

Therefore the scientifically clean next step is **not** to force an existing secondary dataset into the primary role. The primary evidence should be generated through the already-provisional prospective controlled transaction-episode design, with ETI exposure assigned independently of O1 and with all event-level evidence retained.

This is a research-design decision, not a validation result.
