# DEETI R1 Candidate Source Screening v1

**Status:** PROVISIONAL — NOT FROZEN
**Scientific status:** R0

## Purpose

Screen candidate real-world evidence sources before inspecting confirmatory outcome results.

## Candidate source classes

### A. Controlled escrow experiment

A prospective experiment comparing the same economic transaction under baseline control versus an escrow-enabled treatment.

**Primary suitability:** High.

Required evidence:
- treatment assignment;
- transaction initiation;
- declared conditions;
- independent evidence of Trust, Transparency, and Verified Fulfilment;
- settlement/refund event;
- independent O1 coding;
- provenance.

### B. Existing escrow adoption experiment

Historical experimental data where participants choose or are assigned to escrow and settlement outcomes are observed.

**Suitability:** Potentially high, subject to ETI reconstructability.

Critical risk: historical escrow may not expose all three ET components as separately measurable constructs.

### C. Digital marketplace transaction data

Real transaction episodes with escrow/payment and dispute records.

**Suitability:** Potentially high for O1, but ETI reconstruction may be limited.

### D. SHUUD/SHIID transaction data

Real minor-incident insurance/escrow transaction episodes.

**Suitability:** Later replication/application domain.

It is not the first foundational test because road, insurance, operator, AI, and user variables can confound the effect.

### E. Framework simulation / synthetic workload

Useful for mechanism verification and engineering experiments.

**Suitability for primary scientific claim:** Exploratory only.

Synthetic settlement rates cannot establish a real-world foundational capability.

## Critical screening rule

A candidate cannot be PRIMARY_ELIGIBLE unless:

`O1Reconstructable ∧ ETIReconstructable ∧ ETI_O1_Separated ∧ ProvenanceComplete ∧ NegativeEvidenceAvailable ∧ TemporalOrderingValid`

## Decision labels

- PRIMARY_ELIGIBLE
- SECONDARY_ONLY
- EXPLORATORY_ONLY
- REJECTED

## Selection discipline

The candidate source must be classified before confirmatory outcome inspection. Outcome performance must not be used to select the preferred source.

## Current provisional direction

The preferred primary class is **A: controlled escrow experiment**, because it offers the cleanest test of whether adding Escrow Trinity capability changes transaction reliability while holding the underlying economic task constant.

Historical escrow experiments may be used as design precedent or secondary evidence unless their data structure permits full ETI reconstruction without leakage.

Current state: **R0 / PROVISIONAL**.
