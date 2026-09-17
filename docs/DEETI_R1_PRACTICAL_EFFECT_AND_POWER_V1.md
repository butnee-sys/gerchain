# DEETI R1 Practical Effect and Power Specification v1

**Status:** R1 preparation
**Scientific status:** R0 until the complete R1 gate is evidenced
**Date:** 2026-09-17

## 1. Purpose

A statistically detectable association is not sufficient to establish a useful Digital Economy capability. The first confirmatory study therefore requires a pre-specified minimum practically meaningful change in O1.

## 2. Primary outcome

`O1 = completed governed transactions / initiated governed transactions`

Let the baseline completion probability be `p0` and the minimum practically meaningful absolute improvement be `δ`.

The target alternative is:

```text
p1 = p0 + δ
```

The value of `δ` must be justified from the operational/economic context of the study and frozen before confirmatory outcome inspection.

## 3. Binary-outcome sample-size calculation

For a simple two-independent-group comparison of proportions, an initial planning approximation is:

```text
n = [
    z_(1-α/2) * sqrt(2*p̄*(1-p̄))
    + z_(1-β) * sqrt(p0*(1-p0) + p1*(1-p1))
]^2 / (p1-p0)^2
```

where:

```text
p̄ = (p0 + p1) / 2
α  = two-sided type-I error rate
β  = type-II error rate
1-β = statistical power
```

This is a planning approximation only. The final calculation must match the actual primary design, clustering, allocation, repeated observations, and analysis model.

## 4. Illustrative planning scenarios

These are **not empirical claims** and must not enter the evidence dataset.

| Baseline p0 | Practical improvement δ | Target p1 |
|---:|---:|---:|
| 0.80 | 0.05 | 0.85 |
| 0.80 | 0.03 | 0.83 |
| 0.90 | 0.03 | 0.93 |
| 0.90 | 0.02 | 0.92 |

The final scenario must be selected using domain evidence before confirmatory analysis.

## 5. Why δ must not be selected from the data

Choosing the smallest observed difference that produces statistical significance would bias the study toward finding support for H1.

The correct order is:

```text
Substantive justification
→ δ frozen
→ power/sample-size calculation
→ sampling
→ outcome observation
→ analysis
```

## 6. Multiple-testing protection

O1 remains the single primary endpoint for the first confirmatory test. O2–O5 remain secondary unless separately registered.

The primary α level must be frozen before confirmatory testing.

## 7. Design-adjustment requirements

The simple two-group formula must be adjusted when applicable for:

- unequal allocation;
- clustering/design effect;
- repeated observations;
- attrition or unusable observations;
- stratification/matching;
- covariate-adjusted analysis;
- non-independent transaction episodes.

## 8. Power simulation requirement

For the actual planned model, simulation is preferred when analytical power formulas do not accurately represent the design.

Simulation inputs must be versioned and include:

```text
baseline outcome rate
ETI distribution
ETI-outcome effect assumed for planning
covariate distributions
cluster structure
sample size
α
power target
missingness/attrition assumptions
```

The simulation must be run before the confirmatory sample is finalized.

## 9. R1 freeze gate

```text
PrimaryOutcomeFrozen
∧ AlphaFrozen
∧ PracticalEffectδFrozen
∧ DesignFrozen
∧ PowerTargetFrozen
∧ SampleSizeMethodFrozen
∧ MissingnessAdjustmentFrozen
```

Passing this gate means the study is statistically planned. It does not mean H1 is supported.
