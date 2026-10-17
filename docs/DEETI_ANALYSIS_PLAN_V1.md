# DEETI Confirmatory Analysis Plan v1

**Status:** Pre-analysis specification — R1 preparation
**Date:** 2026-09-17
**Research status:** R0 — hypothesis registered, not validated

## 1. Primary estimand

The primary estimand is the change in the pre-specified primary Digital Economy outcome associated with a one-unit increase in ETI, after adjustment for pre-specified confounders.

If a controlled intervention exists, the preferred estimand is the average treatment effect of increasing ET capability relative to the defined counterfactual.

## 2. Primary model

For a continuous primary outcome:

```text
Y_i = β0 + β1·ETI_i + β2·Complexity_i + β3·Value_i + β4·Maturity_i + γ_domain + γ_time + ε_i
```

The coefficient of interest is `β1`.

For binary outcomes, an appropriate generalized linear model is used. For clustered or longitudinal observations, the model must account for the relevant clustering/time structure.

## 3. Component model

Estimate:

```text
Y = β0 + βT·T + βTr·Tr + βTf·Tf + Controls + ε
```

This separates the contribution of the three ET components.

## 4. Complementarity test

Estimate:

```text
Y = β0 + βT·T + βTr·Tr + βTf·Tf
    + βTTr·T·Tr
    + βTTf·T·Tf
    + βTrTf·Tr·Tf
    + Controls + ε
```

A positive and practically meaningful interaction pattern is required before claiming that the three components operate as a complementary capability.

## 5. Ablation test

Compare the full model with models excluding each component:

```text
Full: T + Tr + Tf
A:    Tr + Tf
B:    T + Tf
C:    T + Tr
```

The predicted foundational claim is weakened if removal of a component produces no meaningful change in the primary outcome.

## 6. Practical significance

Statistical significance alone is insufficient.

Before confirmatory analysis, a minimum practically meaningful effect size must be registered for the primary outcome. If the estimated effect is statistically detectable but below that threshold, the result is classified as **statistically detectable but practically insufficient**.

## 7. Diagnostics

Required diagnostics include:

- model specification checks;
- residual diagnostics where applicable;
- multicollinearity checks;
- influential-observation analysis;
- missing-data sensitivity;
- heterogeneity by domain and transaction complexity;
- alternative ETI weighting.

## 8. Robustness

Repeat the primary analysis with:

1. equal ETI weights;
2. empirically estimated weights;
3. alternative normalization;
4. alternative complexity controls;
5. alternative reasonable time windows;
6. exclusion/inclusion of influential observations;
7. alternative outcome definitions.

## 9. Multiple outcomes

O1–O5 are not all primary endpoints. One primary endpoint must be frozen before confirmatory testing. Remaining outcomes are secondary and exploratory unless separately registered.

## 10. Missing and excluded observations

Missingness rules must be fixed before outcome inspection. Exclusions require documented criteria and a retained exclusion log.

## 11. Negative-result rule

The analysis must preserve and report null, adverse, and contradictory findings. No post-hoc redefinition of ETI or outcomes is permitted solely to rescue H1.

## 12. R1 analysis-freeze gate

```text
PrimaryEndpointFrozen
∧ ETIFormulaFrozen
∧ ControlsFrozen
∧ ModelFamilyFrozen
∧ PracticalEffectThresholdFrozen
∧ MissingDataRuleFrozen
∧ ExclusionRuleFrozen
∧ RobustnessSetFrozen
```

Only after this gate is met can the project advance from measurement preparation toward confirmatory empirical testing.
