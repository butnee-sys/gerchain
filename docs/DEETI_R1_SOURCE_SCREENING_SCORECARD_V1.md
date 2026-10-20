# DEETI R1 Source Screening Scorecard v1

**Status:** R1 preparation
**Scientific status:** R0

## Purpose

Provide a transparent pre-outcome screening mechanism for candidate empirical sources. This scorecard does not select a source by statistical result.

## Critical gates

A candidate source is **ineligible for primary confirmatory use** if any critical gate fails:

- O1 cannot be independently reconstructed;
- ETI cannot be reconstructed independently of O1;
- provenance is not traceable;
- negative/failure observations are systematically unavailable;
- comparison membership is outcome-dependent;
- temporal ordering is incompatible with the intended interpretation.

## Non-critical dimensions

For sources passing all critical gates, record qualitative evidence for:

| Dimension | Question |
|---|---|
| Coverage | Does the source cover the target population and period? |
| Variation | Is there sufficient ETI variation? |
| Precision | Are timestamps and lifecycle events sufficiently precise? |
| Reproducibility | Can an independent analyst rebuild the dataset? |
| Independence | Can O1 be checked against an independent record? |
| Feasibility | Can the source be legally and practically obtained? |
| Stability | Are definitions stable or versioned? |

## Decision categories

```text
PRIMARY_ELIGIBLE
SECONDARY_ELIGIBLE
EXPLORATORY_ONLY
REJECTED
```

No candidate is upgraded because its preliminary results favor H1.

## Freeze requirement

The selected source and all critical screening decisions must be versioned before confirmatory outcome inspection.
