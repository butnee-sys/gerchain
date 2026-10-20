# DEETI R1 Data Collection Protocol v1

**Status:** R1 preparation — data acquisition specification
**Date:** 2026-09-17
**Research status:** R0 until the complete R1 gate is satisfied

## 1. Observation unit

One observation is one governed digital-economic transaction or transaction episode with a uniquely traceable lifecycle.

A transaction episode may contain initiation, verification, condition evaluation, execution, settlement, and closure events.

## 2. Minimum required observation fields

Each record must contain:

```text
observation_id
domain
jurisdiction
period
ET component measurements
ETI
transaction value
transaction complexity
verification time
completion time
settlement delay
failure/dispute status
evidence status
condition verification status
settlement correctness
data source
source version
```

## 3. Eligible evidence

Priority order:

1. machine-generated transaction/event records;
2. independently retained audit records;
3. institutional administrative records;
4. independently verifiable research datasets;
5. structured human coding only where necessary and with inter-rater assessment.

Unverifiable anecdotal claims are not sufficient for the primary analysis.

## 4. Comparison requirement

The dataset must contain variation in ETI sufficient to compare observations with different measured ET capability.

At least one of the following designs must be available before confirmatory testing:

- ET-enabled versus defined non-ET comparison;
- high versus low ETI under a pre-specified threshold;
- longitudinal before/after design;
- quasi-experimental comparison;
- randomized or controlled intervention.

The strongest available design should be selected before outcome inspection.

## 5. Control variables

The minimum pre-specified controls are:

- transaction value;
- transaction complexity;
- technology/process maturity;
- domain;
- jurisdiction/institutional environment;
- period;
- participant or counterparty exposure where measurable;
- transaction volume where relevant.

Additional controls require substantive justification and versioned registration before confirmatory analysis.

## 6. Sampling rule

Sampling must be defined independently of the observed O1 outcome. The sampling frame, inclusion criteria, exclusion criteria, time window, and target sample size/power rule must be recorded before confirmatory outcome analysis.

## 7. Provenance rule

Every observation must be traceable to its source and version. Transformations must be reproducible.

```text
Raw source
→ extraction
→ transformation
→ measurement
→ analysis dataset
```

No manual alteration of the analysis dataset is permitted without a retained transformation record.

## 8. Synthetic-data rule

Synthetic or simulated observations may be used to test software, formulas, validators, and analysis code. They must never be presented as empirical evidence and must remain separated from the real evidence dataset.

## 9. Missing-data rule

Missingness must be classified before confirmatory analysis:

- structurally not applicable;
- unavailable;
- invalid;
- genuinely missing.

The treatment of each category must be frozen before inspecting the primary outcome distribution.

## 10. R1 data-readiness gate

```text
ObservationUnitFrozen
∧ RequiredFieldsDefined
∧ EvidenceEligibilityDefined
∧ ComparisonDesignDefined
∧ ControlsDefined
∧ SamplingRuleDefined
∧ ProvenanceRuleDefined
∧ SyntheticDataSeparated
∧ MissingDataRuleDefined
```

Passing this gate establishes data-collection readiness, not empirical support for H1.
