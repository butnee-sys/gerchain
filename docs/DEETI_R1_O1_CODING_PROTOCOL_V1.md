# DEETI R1 O1 Coding Protocol v1

**Status:** R1 preparation
**Scientific status:** R0
**Date:** 2026-09-17

## 1. O1 definition

```text
O1 = completed governed transactions / initiated governed transactions
```

O1 is measured at the transaction-episode level.

## 2. Initiated transaction

An observation enters the denominator only when the minimum pre-specified initiation event has occurred and a unique `observation_id` can be assigned.

A merely attempted page load, incomplete draft, duplicate event, or test fixture is not an initiated transaction.

## 3. Completed transaction

An observation enters the numerator only when all pre-specified completion conditions are satisfied:

1. required conditions were evaluated;
2. required execution occurred;
3. required settlement/closure event occurred;
4. no unresolved material failure invalidates completion at the defined observation cutoff.

The completion definition must be identical across comparison groups.

## 4. Failure

A transaction is coded as failed when an initiated transaction does not reach the frozen completion state within the defined observation window or reaches an explicitly defined terminal failure state.

## 5. Dispute

A dispute flag is recorded separately from completion. A disputed transaction is not automatically coded as failed unless the pre-specified completion rule makes the dispute outcome incompatible with completion.

## 6. Duplicate and retry handling

Repeated events belonging to one transaction episode must be collapsed using the frozen episode identifier. Retries must not inflate the denominator or numerator.

## 7. Censoring

If completion cannot yet be determined because the observation window has not elapsed, the record is censored rather than automatically coded as failure.

The censoring rule must be applied identically to all comparison groups.

## 8. Auditability

For every O1 coding decision, the dataset must retain sufficient event identifiers to reconstruct:

```text
initiation → conditions → execution → settlement/closure → final O1 state
```

## 9. Inter-rater validation

Where human coding is required, a pre-specified sample must be independently coded by at least two coders. Agreement must be measured before the primary confirmatory analysis.

## 10. No outcome-dependent coding

Coders must not know the final ETI or comparison-group result when this knowledge could influence O1 classification.

## 11. Gate

```text
InitiationRuleFrozen
∧ CompletionRuleFrozen
∧ FailureRuleFrozen
∧ DisputeRuleFrozen
∧ DuplicateRuleFrozen
∧ CensoringRuleFrozen
∧ AuditTrailDefined
∧ HumanCodingValidationDefined
```
