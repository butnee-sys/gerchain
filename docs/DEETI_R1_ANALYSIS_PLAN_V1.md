# DEETI R1 Analysis Plan v1

**Status:** R1 preparation — confirmatory analysis specification
**Date:** 2026-09-17

## 1. Primary estimand

The primary estimand is the change in the pre-specified primary Digital Economy outcome associated with a one-unit increase in ETI on the `[0,1]` scale, under the declared comparison design.

No causal language is permitted for observational designs.

## 2. Primary model

For continuous primary outcomes:

```text
Y_i = β0 + β1·ETI_i + β2·Complexity_i + β3·Value_i + β4·Maturity_i + γ_domain + γ_period + ε_i
```

For binary outcomes, use an appropriate generalized linear model with the same pre-specified covariate logic.

Primary parameter:

```text
β1
```

Interpretation depends on the design and link function.

## 3. Component model

Estimate:

```text
Y = β0 + βT·T + βTr·Tr + βTf·Tf + controls + ε
```

and an interaction model:

```text
Y = β0 + βT·T + βTr·Tr + βTf·Tf
    + βTTr·T·Tr
    + βTTf·T·Tf
    + βTrTf·Tr·Tf
    + controls + ε
```

This tests whether the combined ET structure behaves differently from the sum of independent components.

## 4. Ablation analysis

Where experimental or quasi-experimental data permit, compare:

```text
Full ET
ET - Trust
ET - Transparency
ET - Verified Fulfilment
```

The ablation effect is measured against the same baseline and outcome definition.

## 5. Practical significance

Before confirmatory testing, define a minimum practically meaningful effect `δ` for the primary outcome.

Decision logic:

```text
statistical evidence alone ≠ practical evidence
```

An estimate that is statistically detectable but below `δ` is not treated as practically important.

## 6. Model diagnostics

Required checks:

- residual/fit diagnostics where applicable;
- influential observations;
- collinearity;
- heteroskedasticity;
- clustering dependence;
- temporal dependence;
- missingness mechanism;
- model specification sensitivity.

## 7. Robustness hierarchy

Results must be repeated under:

1. equal ETI weights;
2. alternative justified weights;
3. alternative normalization;
4. alternative control sets;
5. alternative domain subsets;
6. alternative time windows;
7. exclusion of influential observations;
8. missing-data alternatives.

## 8. Multiple outcomes

Only one primary outcome may be designated for the primary confirmatory claim. O2–O5 are secondary unless one is explicitly pre-registered as primary before analysis.

Multiple secondary tests require an appropriate multiplicity strategy or must be labelled exploratory.

## 9. Replication requirement

An internal result advances only to **R2 — Internal empirical test**. It does not establish the foundational claim.

A stronger status requires independent replication:

```text
R2 → R3
```

## 10. Analysis freeze gate

```text
PrimaryOutcomeFrozen
∧ EstimandFrozen
∧ ModelFrozen
∧ CovariatesFrozen
∧ PracticalThresholdFrozen
∧ MissingDataRuleFrozen
∧ RobustnessSetFrozen
```

Until this gate is satisfied, confirmatory analysis must not be described as final.
