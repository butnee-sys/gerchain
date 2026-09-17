# DEETI R1 — Economic Consequence Data Template v1

**Status:** PROVISIONAL — R0 / R1 preparation. NOT FROZEN.  
**Purpose:** establish the minimum empirical record required to derive a defensible practical-effect threshold δ for the DEETI foundational-capability test.

## 1. Primary transaction environment

The initial candidate environment is a **generic digital marketplace escrow transaction**:

- one buyer;
- one seller;
- one digital transaction episode;
- a declared transaction value;
- a verifiable delivery/fulfilment condition;
- an escrow or conditional-settlement mechanism;
- an independently observable terminal state.

This is a research environment, not a claim about any particular marketplace.

SHUUD/SHIID remains a later application-domain replication and is not used to define the foundational δ.

## 2. Economic consequence record

For each transaction episode, record separately:

| Variable | Meaning |
|---|---|
| `transaction_value` | Contracted economic value |
| `direct_failure_cost` | Direct monetary loss caused by failed fulfilment |
| `delay_hours` | Additional elapsed time attributable to delay |
| `delay_cost` | Monetary value attributable to delay |
| `dispute_cost` | Direct cost of dispute/recovery process |
| `recovery_cost` | Cost required to restore the intended transaction state |
| `opportunity_cost` | Measurable foregone economic activity attributable to failure/delay |
| `et_operating_cost` | Incremental cost of providing the ET capability |
| `total_consequence_cost` | Pre-specified non-overlapping aggregate consequence |
| `source_id` | Provenance identifier |
| `source_version` | Source/version used |
| `coding_version` | Coding rule version |

## 3. Non-double-counting rule

The aggregate consequence must not simply sum correlated estimates.

Where delay produces lost output and that lost output is already included in a direct loss estimate, the same loss must not be counted twice.

A transaction may therefore contain:

```text
Direct loss
+ OR delay-derived loss
+ OR dispute/recovery loss
+ OR opportunity loss
```

only where the components are empirically separable.

## 4. Expected consequence

For a declared transaction environment:

\[
E(C_F)=\sum_j P(F_j)C(F_j)
\]

where each mutually exclusive failure state \(F_j\) has an independently measured probability and consequence.

The incremental economic cost of ET is:

\[
E(C_{ET}) = C_{implementation}+C_{operation}+C_{verification}+C_{settlement}\;adjusted\;for\;any\;avoided\;costs\;that\;are\;not\;already\;included\;in\;the\;outcome\;model.
\]

The practical-effect threshold is then derived from the minimum improvement required for the ET capability to be economically decision-relevant.

## 5. Candidate δ derivation

For a binary primary outcome O1:

\[
O1=\frac{completed\ transactions}{initiated\ transactions}
\]

and:

\[
\delta = O1_{ET}-O1_{Control}.
\]

A candidate threshold must satisfy both:

1. **Operational meaning:** the improvement changes transaction reliability in a way that matters to the selected environment.
2. **Economic meaning:** the expected avoided consequence is sufficient to justify the incremental ET cost.

No δ value is frozen by this template.

## 6. Evidence hierarchy

Preferred evidence, in descending order:

1. transaction-level operational records;
2. audited dispute/recovery records;
3. independently collected transaction-cost observations;
4. validated research datasets with reconstructable transaction episodes;
5. published empirical estimates from genuinely comparable environments;
6. expert estimates only where empirical evidence is unavailable, explicitly marked as uncertain.

Synthetic values may be used for code validation and power simulations, but **cannot freeze δ or support the confirmatory foundational claim**.

## 7. Source integrity

Every economic-consequence observation must retain:

- source;
- source version/date;
- extraction rule;
- unit conversion;
- inclusion/exclusion rule;
- transformation code/version;
- uncertainty or confidence interval where available.

The outcome must not be inspected and then used to retrospectively select the economic threshold.

## 8. Required next empirical collection

Before δ can be frozen, the research team must obtain enough observations to estimate:

\[
P(F_j),\quad C(F_j),\quad E(C_{ET})
\]

for the selected transaction environment.

At minimum this requires a defensible estimate of:

- failed-fulfilment frequency;
- delayed-settlement frequency and duration;
- dispute frequency and resolution burden;
- direct monetary loss;
- incremental ET operating cost.

## 9. Falsification condition

The foundational claim must remain falsifiable.

The protocol will be considered unable to support the foundational claim if, after pre-specification and valid measurement:

- no economically meaningful δ can be justified;
- ET cost exceeds any plausible avoided consequence across the relevant range;
- observed reliability improvement is below the frozen practical threshold;
- the effect disappears after legitimate controls;
- or an alternative mechanism explains the observed improvement equally well or better.

## 10. Current gate

```text
TransactionEnvironmentDefined        = YES (provisional)
EconomicVariablesDefined             = YES
NonDoubleCountingRuleDefined         = YES
SourceHierarchyDefined               = YES
ActualEmpiricalValues                = NO
DeltaFrozen                          = NO
PowerFrozen                          = NO
R1_GREEN                             = NO
```

**This document is a measurement template, not empirical validation.**
