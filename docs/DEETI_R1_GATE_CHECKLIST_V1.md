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

- [x] One primary outcome selected and frozen: O1 — transaction reliability
- [x] O1–O5 secondary/exploratory status explicitly recorded
- [ ] Outcome coding rules frozen

## D. Analysis definition

- [x] Primary estimand specified
- [x] Default design hierarchy and identification assumptions registered
- [ ] Actual comparison design frozen for the empirical dataset
- [ ] Primary model family frozen for the selected comparison design
- [ ] Covariates frozen
- [ ] Practical-effect threshold frozen
- [ ] Alpha level frozen
- [ ] Sample-size/power rule frozen
- [ ] Missing-data rule frozen
- [ ] Robustness set frozen

## E. Evidence integrity

- [ ] Source identifier required and implemented
- [ ] Source version required and implemented
- [ ] Collection timestamp required and implemented
- [ ] Transformation version required and implemented
- [ ] Measurement version required and implemented
- [ ] Exclusion log retained
- [ ] Negative/contradictory observations retained

## F. Reproducibility

- [ ] Dataset validator passes against the complete empirical dataset
- [ ] ETI is recomputable from components
- [x] No synthetic data in empirical dataset
- [ ] Analysis can be rerun from versioned inputs

## Gate predicate

```text
R1 = A ∧ B ∧ C ∧ D ∧ E ∧ F
```

If any item is unchecked, status remains **R0**.

## Scientific decision rule

R1 is a measurement-readiness gate only. Passing R1 does **not** support H1. H1 can only be evaluated after empirical testing and falsification analysis.

## Current blockers

1. Freeze the actual comparison design for the selected evidence source.
2. Freeze the practical minimum effect threshold before inspecting confirmatory outcomes.
3. Freeze alpha and the design-specific sample-size/power rule.
4. Execute measurement validation.
5. Implement and verify complete provenance fields.
6. Validate analysis code against separated synthetic fixtures.
7. Obtain and version real empirical observations.
