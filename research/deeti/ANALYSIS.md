# DEETI empirical execution order

## Gate 0 — Data integrity

Run:

```bash
python research/deeti/validate_dataset.py
```

The expected empty-dataset result is schema validation only. No empirical conclusion may be drawn from an empty dataset.

## Gate 1 — Freeze measurement

Confirm the R1 measurement dictionary and analysis plan have not changed after outcome inspection.

## Gate 2 — Load real evidence

Populate `data/deeti_evidence_v1.csv` only with traceable observations. Do not insert invented or synthetic observations.

## Gate 3 — Primary test

Estimate the pre-specified relationship between ETI and the primary outcome with the frozen controls.

## Gate 4 — Component tests

Estimate T, Tr, and Tf separately, then perform the pre-specified ablation and interaction tests.

## Gate 5 — Robustness

Run the registered alternative weighting, normalization, control, window, exclusion, and outcome specifications.

## Gate 6 — Classification

Use only these statuses:

- `NOT_SUPPORTED`
- `INCONCLUSIVE`
- `EMPIRICALLY_SUPPORTED`

Do not use `GREEN` as a scientific validation label.

## Gate 7 — Replication

An internally positive result is not sufficient for R3. Independent replication is required.
