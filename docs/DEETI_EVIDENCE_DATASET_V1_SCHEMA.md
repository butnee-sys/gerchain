# DEETI Evidence Dataset v1 — Research Data Schema

**Status:** R1 preparation — measurement specification
**Date:** 2026-09-17
**Research protocol:** `docs/DEETI_FOUNDATIONAL_CAPABILITY_RESEARCH_PROTOCOL_V1.md`

## 1. Purpose

This schema defines the minimum observation structure required to move the DEETI research program from **R0 — Registered hypothesis** toward **R1 — Operationalized measurement model**.

It does not claim empirical validation.

## 2. Unit of observation

Preferred unit:

> **one governed digital economic transaction / transaction episode**

Where transaction-level data are unavailable, the protocol permits system-period observations, but the analysis must clearly distinguish transaction-level and aggregate evidence.

## 3. Required fields

| Field | Meaning | Type |
|---|---|---|
| `observation_id` | Unique observation identifier | string |
| `domain` | Transaction domain | categorical |
| `jurisdiction` | Legal/economic environment | categorical |
| `period` | Observation period | date/time |
| `et_trust` | Trust component score | [0,1] |
| `et_transparency` | Transparency component score | [0,1] |
| `et_fulfilment` | Verified fulfilment score | [0,1] |
| `eti` | Composite ET capability index | [0,1] |
| `transaction_value` | Economic value involved | numeric |
| `transaction_complexity` | Pre-specified complexity measure | numeric |
| `verification_time` | Time required for verification | numeric |
| `completion_time` | Time to completed outcome | numeric |
| `settlement_delay` | Delay to settlement | numeric |
| `failure_flag` | Failed transaction indicator | binary |
| `dispute_flag` | Dispute indicator | binary |
| `evidence_complete` | Evidence reconstructability | binary |
| `condition_verified` | Conditions verified | binary |
| `correct_settlement` | Correct authorized settlement | binary |
| `direct_cost` | Direct transaction cost | numeric |
| `control_group` | Comparison-group indicator | categorical |
| `data_source` | Source identifier | string |
| `source_version` | Source/data vintage | string |

## 4. Primary derived outcomes

```text
O1 = successful_completion_rate
O2 = transaction_friction
O3 = failure_or_dispute_rate
O4 = evidence_integrity_rate
O5 = conditional_settlement_performance
```

## 5. ETI construction

Primary specification:

```text
ETI = (et_trust + et_transparency + et_fulfilment) / 3
```

Alternative weighting must be treated as a robustness specification, not substituted after observing the outcome.

## 6. Minimum comparison requirement

The dataset is not considered sufficient for causal testing unless it contains at least one credible comparison between materially different ET capability levels.

Preferred order:

1. controlled intervention;
2. quasi-experimental comparison;
3. matched high-ET / low-ET observations;
4. longitudinal before/after observations;
5. cross-sectional observational comparison.

## 7. Data integrity requirements

Every observation must retain source, source version/date, transformation history, inclusion/exclusion status, missing-value treatment, calculation version, and reproducible identifier.

No manually edited result should enter the confirmatory dataset without an auditable transformation record.

## 8. Negative evidence

The dataset must preserve failed transactions, disputes, incomplete evidence, failed verification, and failed fulfilment. Excluding negative observations because they weaken the hypothesis is prohibited.

## 9. R1 gate

The project may advance to **R1** only when:

```text
SchemaDefined
∧ VariablesOperationalized
∧ PrimaryEndpointPreSpecified
∧ ComparisonDefined
∧ DataDictionaryComplete
∧ TransformationTraceable
```

Until then:

```text
Research Status = R0
```
