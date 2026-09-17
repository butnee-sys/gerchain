# DEETI Empirical Research Workspace v1

**Status:** R0 / R1 preparation. No empirical validation claimed.

This directory is the reproducible workspace for testing:

```text
ET = Trust + Transparency + Verified Fulfilment
                  ↓
        DE foundational capability ?
```

## Files

- `data/deeti_evidence_v1.csv` — empty, schema-only evidence table; no invented observations.
- `validate_dataset.py` — validates required fields and recomputes ETI from component scores.
- `ANALYSIS.md` — execution order for the pre-specified analysis plan.

## Rule

Real observations must enter with traceable source and source version. Synthetic observations may be used only for software tests and must never be mixed into the empirical dataset.
