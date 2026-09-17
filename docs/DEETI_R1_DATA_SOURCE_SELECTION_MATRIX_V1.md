# DEETI R1 Data Source Selection Matrix v1

**Status:** R1 preparation
**Scientific status:** R0
**Date:** 2026-09-17

## 1. Purpose

Select an empirical evidence source before confirmatory outcome inspection, using explicit criteria rather than convenience.

## 2. Selection dimensions

Each candidate source is assessed on:

| Dimension | Required question |
|---|---|
| O1 observability | Can initiation and completion be identified independently? |
| ETI observability | Can Trust, Transparency and verified fulfilment be measured without redefining them from O1? |
| Temporal order | Is ETI exposure/measurement temporally ordered relative to O1? |
| Variation | Is there sufficient variation in ETI? |
| Comparison | Is there a credible lower/no-ET comparison or intervention? |
| Provenance | Can observations be traced to source records? |
| Independence | Is O1 independently verifiable? |
| Coverage | Does the source cover the target population and period? |
| Stability | Are definitions stable across the observation window? |
| Reproducibility | Can an independent analyst reconstruct the dataset? |

## 3. Exclusion triggers

A source is excluded from primary confirmatory use if:

1. O1 cannot be reconstructed;
2. ETI is defined using the same outcome in a circular way;
3. treatment/exposure and outcome timing cannot be separated where causal interpretation is intended;
4. source provenance is unverifiable;
5. critical variables are systematically unavailable for one comparison group;
6. definitions change without a reconstructable version history.

## 4. Preferred evidence architecture

The strongest candidate source has:

```text
Independent event records
        ↓
ETI measurement
        ↓
O1 reconstruction
        ↓
Independent audit/re-performance
```

A source that only supplies aggregated success percentages without transaction-level provenance is insufficient for the primary transaction-level protocol.

## 5. Candidate-source scoring

A numerical score must not be used to override exclusion triggers. After exclusions, remaining sources may be compared using a pre-specified qualitative decision matrix.

The selected source must document:

```text
source_id
coverage
limitations
comparison structure
ETI availability
O1 availability
independent verification
```

## 6. Freeze rule

The primary evidence source must be selected before confirmatory outcome inspection. A later source change requires a new versioned protocol and must be treated as exploratory for the existing dataset.

## 7. Gate

```text
CandidatesDefined
∧ ExclusionRulesApplied
∧ O1Observable
∧ ETIObservable
∧ TemporalOrderDefined
∧ ComparisonAvailable
∧ ProvenanceVerified
∧ IndependenceAssessed
∧ SourceFrozenBeforeOutcomeInspection
```

Passing this gate establishes source readiness, not empirical support for H1.
