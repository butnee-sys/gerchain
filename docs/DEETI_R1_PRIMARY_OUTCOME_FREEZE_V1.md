# DEETI R1 Primary Outcome Freeze v1

**Status:** R1 preparation — pre-analysis decision record
**Date:** 2026-09-17
**Research status:** R0 until the complete R1 gate is satisfied

## 1. Decision

The primary outcome for the first confirmatory DEETI test is:

> **O1 — Transaction Reliability**

Operational definition:

```text
O1 = completed governed transactions / initiated governed transactions
```

The unit of observation remains one governed digital-economic transaction or transaction episode.

## 2. Why O1 is primary

The foundational claim being tested is not that ET merely improves perception, convenience, or documentation. The claim is that:

```text
ET capability
      ↓
more reliable digital-economic activity
```

O1 therefore measures the most direct first-order consequence of the proposed foundational capability: whether initiated governed transactions reach the defined completion state.

The outcome is external to the ETI construction and therefore provides a cleaner separation between the explanatory construct and the target outcome than an outcome that is itself an ET component.

## 3. Why the other outcomes remain secondary

### O2 — Friction

Important for practical value, but transaction time and cost can be affected by many operational factors unrelated to ET capability. It remains a secondary outcome.

### O3 — Failure/dispute

Highly relevant and expected to be associated with reliability, but it overlaps conceptually with the complement of completion/failure and is therefore secondary in the first test.

### O4 — Evidence integrity

Central to Transparency, so making it the primary outcome would risk circularity because evidence integrity is also part of the explanatory ET construct.

### O5 — Conditional settlement performance

Important for escrow execution, but narrower than the general Digital Economy foundational claim and more closely tied to settlement architecture.

## 4. Primary interpretation rule

A positive association between ETI and O1 is evidence consistent with the hypothesis, not proof of a universal foundational law.

For causal interpretation, the study must use a design that identifies a credible counterfactual. Observational association alone must be reported as association.

## 5. Falsification rule

The foundational-capability claim is weakened or rejected for the tested population/design if:

1. ETI has no practically meaningful relationship with O1;
2. the relationship disappears after the pre-specified controls;
3. the result is driven by a narrow specification or influential observations;
4. removal of an ET component produces no meaningful deterioration where component necessity is claimed;
5. a credible alternative explanation accounts for the observed relationship equally well or better;
6. an intervention intended to increase ET capability produces no improvement in O1 when a causal test is available;
7. independent replication fails.

## 6. No post-hoc substitution rule

O2, O3, O4, or O5 must not replace O1 as the primary endpoint merely because they produce a stronger or more convenient result after data inspection.

Any later change requires a new versioned pre-analysis decision record and is exploratory for the existing dataset.

## 7. R1 gate implication

The primary endpoint is now specified as O1 for the first confirmatory protocol. R1 is still **not declared complete** until the remaining analysis-freeze conditions are satisfied.

```text
PrimaryEndpoint = O1
```
