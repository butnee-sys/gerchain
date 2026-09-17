# DEETI R1 Comparison Design v1

**Status:** Design specification
**Scientific status:** R0 — not yet selected for confirmatory execution
**Date:** 2026-09-17

## 1. Design question

The first empirical test must distinguish whether measured ET capability is associated with transaction reliability beyond ordinary process/technology maturity.

## 2. Candidate designs

### Design A — ET-enabled versus non-ET comparison

Compare otherwise comparable transaction episodes that differ in the presence of the defined ET capability.

Required:
- comparable transaction class;
- common outcome definition;
- pre-specified matching/adjustment variables;
- independent measurement of ETI.

### Design B — Within-system before/after

Compare O1 before and after a documented ET capability intervention.

Required:
- intervention date fixed independently;
- stable outcome definition;
- adequate pre/post observation window;
- interruption/confounding assessment.

### Design C — Quasi-experimental comparison

Use an externally determined change in ET capability with a credible comparison group.

Preferred estimator where assumptions are credible:

```text
Y_it = α + β(Post_t × Treated_i) + unit effects + time effects + controls + ε_it
```

### Design D — Randomized/controlled intervention

Where feasible, randomly assign or otherwise externally control the introduction of an ET mechanism and estimate its effect on O1.

This provides the strongest basis for causal interpretation among the listed designs, subject to implementation quality and compliance.

## 3. Selection rule

The final confirmatory design must be selected **before inspection of confirmatory outcome results**.

Selection priority is based on:

1. credible counterfactual;
2. independent ET variation;
3. outcome observability;
4. temporal ordering;
5. control of confounding;
6. reproducibility;
7. sufficient statistical power.

This is a methodological selection rule, not a ranking of results or institutions.

## 4. Causal-language rule

- Cross-sectional observational data → association only.
- Longitudinal observational data → temporal association unless identification assumptions support stronger inference.
- Quasi-experimental data → causal interpretation only under explicitly tested identification assumptions.
- Randomized/controlled intervention → causal interpretation subject to implementation and analysis assumptions.

## 5. Required falsification checks

The selected design must test:

- pre-trends where applicable;
- balance/comparability where applicable;
- intervention contamination;
- concurrent changes;
- measurement drift;
- attrition/missingness;
- alternative plausible explanations;
- sensitivity to reasonable specification changes.

## 6. Current status

No comparison design is declared final yet.

Therefore:

```text
ComparisonDesignFrozen = FALSE
R1 = NOT COMPLETE
ScientificStatus = R0
```
