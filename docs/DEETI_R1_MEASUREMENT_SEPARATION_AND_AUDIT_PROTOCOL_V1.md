# DEETI R1 Measurement Separation and Audit Protocol v1

**Status:** PROVISIONAL — NOT FROZEN
**Scientific status:** R0

## 1. Purpose

This protocol prevents the primary explanatory variable (ETI) from being constructed from the primary outcome (O1), and makes every transformation independently reproducible.

## 2. ETI measurement domain

ETI consists of three independently evidenced components:

\[
ETI=(T+Tr+Tf)/3
\]

where:

- `T` = Trust capability;
- `Tr` = Transparency capability;
- `Tf` = Verified Fulfilment capability.

Each component must be reconstructed from fields that are not themselves O1.

## 3. O1 measurement domain

\[
O1=Completed/Initiated
\]

Initiation and completion are defined by the independent O1 coding protocol.

The O1 coder must not infer ETI from whether the transaction completed.

## 4. Field-level separation test

Before confirmatory analysis, construct a field map:

```text
ETI fields ───────X──────> O1 fields
O1 fields ────────X──────> ETI fields
```

A field that directly encodes completion, failure, settlement success, or unresolved dispute cannot be used as an ETI component unless a pre-specified theoretical justification and sensitivity analysis are documented.

## 5. Temporal separation

For causal interpretation:

```text
ET assignment / ET exposure
          < t0
          ↓
transaction lifecycle
          ↓
O1 determination
          > t0
```

Post-outcome information cannot be used to construct the treatment-side ETI score.

## 6. Independent audit

At least one independent verifier must be able to reproduce from raw transaction evidence:

1. ETI component scores;
2. ETI aggregate score;
3. initiation status;
4. completion status;
5. final O1 value;
6. transformation/version identifiers.

## 7. Reproducibility requirement

The analysis package must contain:

- source snapshot/version;
- variable dictionary;
- coding rules;
- transformation code;
- ETI calculation code;
- O1 calculation code;
- exclusion log;
- missing-data handling;
- final analysis dataset hash;
- analysis script/version.

A second analyst should be able to regenerate the same ETI and O1 values from the frozen source snapshot.

## 8. Failure conditions

The primary experiment is invalid for confirmatory inference if:

- ETI contains outcome leakage;
- post-outcome information enters ETI;
- O1 coding depends on treatment status;
- source provenance is incomplete;
- independent reproduction cannot recover the reported values.

## 9. R1 gate contribution

This protocol contributes:

`ETI_O1_Separation ∧ TemporalOrdering ∧ IndependentReproduction ∧ TransformationTraceability`.

It does not by itself establish the foundational-capability hypothesis.

Current status: **R0 / PROVISIONAL**.
