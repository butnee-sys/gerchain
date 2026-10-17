# DEETI R1 ETI–O1 Separation Test v1

**Status:** R1 preparation
**Scientific status:** R0
**Date:** 2026-09-17

## 1. Purpose

Before estimating the ETI→O1 relationship, verify that the explanatory construct and primary outcome are not mechanically the same measurement.

## 2. Separation requirements

ETI must be constructed only from its pre-specified Trust, Transparency and verified-fulfilment indicators.

O1 must be constructed only from the independently frozen initiation/completion coding rule.

No O1 indicator may be reused as an ETI component.

No ETI indicator may be inserted into O1 merely because it predicts completion.

## 3. Leakage audit

For every ETI indicator, record:

```text
indicator_id
construct
source_field
transformation
whether_used_in_O1
```

Primary confirmatory analysis is blocked if any ETI indicator is also used directly in O1.

## 4. Temporal audit

Where causal interpretation is intended:

```text
ETI measurement / exposure
        ↓
        t0
        ↓
O1 observation window
        ↓
        t1
```

Post-outcome information cannot be used to construct pre-outcome ETI.

## 5. Independence audit

The person/system coding ETI should not use the final O1 result when that could influence the ETI score.

## 6. Statistical diagnostic

After data collection, inspect the correlation structure among ETI components and O1. Extremely mechanical correlation is a warning signal requiring a measurement audit, not evidence for H1.

## 7. Gate

```text
NoIndicatorOverlap
∧ TemporalOrderValid
∧ NoOutcomeLeakage
∧ CodingIndependenceDefined
∧ TransformationTraceable
```

Passing this gate establishes construct-outcome separation. It does not establish the DEETI hypothesis.
