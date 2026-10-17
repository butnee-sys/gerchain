# DEETI R1 Freeze Record v1

**Status:** R1 preparation — NOT YET FROZEN
**Date:** 2026-09-17

This record defines what must be frozen before empirical outcome inspection. It intentionally contains no empirical result and no selected winning hypothesis.

## Required immutable inputs

1. DEETI hypothesis version.
2. Measurement dictionary version.
3. Evidence dataset schema version.
4. Primary outcome selection.
5. Primary estimand.
6. Primary model family.
7. Covariate list.
8. Practical-effect threshold.
9. Missing-data rule.
10. Exclusion rule.
11. Robustness specification set.
12. Software/environment version.

## Freeze sequence

```text
Hypothesis
→ Measurement
→ Outcome
→ Estimand
→ Model
→ Controls
→ Threshold
→ Missingness
→ Exclusions
→ Robustness
→ Dataset
→ Analysis
```

## Anti-hindsight rule

After confirmatory outcome data are inspected, the frozen definitions above cannot be changed to improve support for H1. Any exploratory change receives a new version and cannot replace the primary confirmatory specification.

## Status rule

```text
R0 = hypothesis registered
R1 = measurement/analysis specification frozen and reproducible
R2 = internal empirical test completed
```

A repository commit containing this document does not itself establish R1. The gate is passed only when all required inputs are actually frozen and evidenced.
