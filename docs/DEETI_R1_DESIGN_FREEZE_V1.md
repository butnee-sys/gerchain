# DEETI R1 Design Freeze v1

**Status:** R1 preparation — design decision record
**Date:** 2026-09-17
**Scientific status:** R0 until all R1 gates are evidenced

## 1. Primary design

For the first empirical study, the default design is a **prospective controlled comparative design** at the transaction-episode level.

The preferred comparison is:

```text
ET-capability exposure
        vs
defined lower/no-ET exposure
```

with outcome O1 measured after the exposure definition is fixed.

If a credible randomized or quasi-experimental implementation is available, it supersedes the simple controlled comparison because it provides stronger counterfactual identification.

## 2. Design hierarchy

Use the strongest feasible design available **before confirmatory outcome inspection**:

1. randomized/controlled intervention;
2. credible quasi-experiment;
3. prospective matched controlled comparison;
4. longitudinal before/after with a defined counterfactual;
5. cross-sectional comparison.

The actual selected design must be documented with inclusion/exclusion criteria and identification assumptions.

## 3. Primary outcome

```text
O1 = completed governed transactions / initiated governed transactions
```

## 4. Primary explanatory variable

```text
ETI = (T + Tr + Tf) / 3
```

where `Tf` is verified fulfilment.

## 5. Primary model family

If observations are independent and O1 is binary at transaction level, use a pre-specified binary-outcome model appropriate to the sampling design.

If the analysis aggregates to rates, use an appropriate binomial model rather than treating proportions as ordinary continuous observations without justification.

For clustered observations, account for clustering at the pre-specified level.

## 6. Identification assumptions

For causal interpretation, the design must explicitly address:

- treatment/exposure assignment;
- temporal ordering;
- confounding;
- selection;
- measurement error;
- interference between observations;
- missingness;
- spillover effects.

Observational designs are interpreted as associations unless a credible identification strategy supports causal interpretation.

## 7. Pre-analysis freeze

Before confirmatory outcome inspection, freeze:

```text
Design
PrimaryOutcome
ETIFormula
Covariates
ModelFamily
Alpha
PracticalEffectThreshold
SampleSizeRule
MissingDataRule
ExclusionRule
RobustnessSet
```

## 8. Falsification implications

The design must be capable of detecting at least one plausible failure of the foundational claim. A design that can only generate supportive evidence but cannot discriminate H1 from credible alternatives is insufficient for confirmatory use.

## 9. Status

This document establishes the default design hierarchy. It does **not** claim that an empirical study has been completed or that DEETI has been validated.

R1 remains incomplete until all checklist conditions are evidenced.
