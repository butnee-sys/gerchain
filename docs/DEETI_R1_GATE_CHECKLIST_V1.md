# DEETI R1 Gate Checklist v1

**Status:** R1 preparation
**Scientific status:** R0 until every gate below is evidenced

## A. Construct definition

- [ ] Trust construct and indicators frozen
- [ ] Transparency construct and indicators frozen
- [ ] Triumph operationalized as verified fulfilment
- [ ] ETI composite formula frozen

## B. Observation definition

- [ ] Unit of observation frozen
- [ ] Inclusion criteria frozen
- [ ] Exclusion criteria frozen
- [ ] Time window frozen
- [ ] Jurisdiction/domain fields defined

## C. Outcome definition

- [ ] One primary outcome selected and frozen
- [ ] O1–O5 secondary/exploratory status explicitly recorded
- [ ] Outcome coding rules frozen

## D. Analysis definition

- [ ] Primary estimand frozen
- [ ] Primary model family frozen
- [ ] Covariates frozen
- [ ] Practical-effect threshold frozen
- [ ] Missing-data rule frozen
- [ ] Robustness set frozen

## E. Evidence integrity

- [ ] Source identifier required
- [ ] Source version required
- [ ] Collection timestamp required
- [ ] Transformation version required
- [ ] Measurement version required
- [ ] Exclusion log retained
- [ ] Negative/contradictory observations retained

## F. Reproducibility

- [ ] Dataset validator passes
- [ ] ETI is recomputable from components
- [ ] No synthetic data in empirical dataset
- [ ] Analysis can be rerun from versioned inputs

## Gate predicate

```text
R1 =
A ∧ B ∧ C ∧ D ∧ E ∧ F
```

If any item is unchecked, status remains **R0**.

## Scientific decision rule

R1 is a measurement readiness gate only. Passing R1 does **not** support H1. H1 can only be evaluated after empirical testing and falsification analysis.
