# DEETI R1 Prospective Experimental Design v1

**Status:** R1 preparation
**Scientific status:** R0 — Registered hypothesis

## 1. Research question

Does exposure to a pre-specified Escrow Trinity capability — Trust, Transparency, and Verified Fulfilment — improve transaction reliability relative to an otherwise comparable transaction process without that capability?

## 2. Unit of observation

One independently identifiable digital-economic transaction episode.

Each episode must have:

- unique transaction identifier;
- initiation timestamp;
- exposure assignment timestamp;
- condition-verification events;
- settlement or failure events;
- evidence references;
- final O1 coding status.

## 3. Experimental comparison

### Treatment

Transaction episodes processed through the pre-specified ET capability:

```text
Trust control
+ Transparency evidence
+ Verified conditional fulfilment
```

### Control

Comparable transaction episodes processed through the same underlying transaction environment but without the ET capability under test.

The control must not receive a hidden substitute mechanism that reproduces the treatment construct.

## 4. Assignment

Preferred design:

```text
Eligible transaction
       ↓
Pre-treatment eligibility check
       ↓
Random assignment
   ↙           ↘
Control      ET treatment
   ↓           ↓
transaction lifecycle
       ↓
independent O1 coding
```

Assignment must occur before outcome realization and must not depend on expected transaction success.

If randomization is impossible, the study must use a pre-specified quasi-experimental or matched prospective design and downgrade causal interpretation accordingly.

## 5. Primary outcome

O1 — transaction reliability:

```text
O1 = completed governed transactions / initiated governed transactions
```

Completion must be coded independently from ETI construction.

## 6. Secondary outcomes

- transaction friction;
- settlement delay;
- failure/dispute rate;
- evidence integrity;
- conditional settlement performance.

## 7. Primary estimand

For a randomized design:

```text
ATE = E[O1 | ET treatment] - E[O1 | control]
```

The confirmatory analysis must report both absolute and relative effects with uncertainty intervals.

## 8. Practical-effect threshold

A minimum decision-relevant absolute improvement δ must be justified and frozen before confirmatory outcome inspection.

No post-hoc δ selection is permitted.

## 9. Sample-size rule

Sample size must be determined from the frozen baseline O1, δ, alpha, target power, allocation ratio, clustering assumptions, and expected attrition/missingness.

The final calculation must be design-specific.

## 10. Blinding / independent coding

Where full participant blinding is impossible, outcome coding should remain independent from treatment assignment where operationally feasible.

The analyst must receive a versioned dataset with treatment labels separated from the primary coding process until the coding dataset is locked.

## 11. Leakage prevention

The following are prohibited:

- using O1 to construct ETI;
- using post-treatment information to define treatment;
- changing completion rules after inspecting outcomes;
- excluding failed transactions after observing failure;
- changing δ after observing effect size;
- changing the primary model because of observed significance.

## 12. Falsification

The foundational capability claim is weakened or rejected if the pre-specified experiment shows:

1. no meaningful O1 improvement;
2. the estimated effect is below the frozen practical threshold;
3. the effect disappears after pre-specified controls or sensitivity tests;
4. component ablation shows no necessity of the ET construct;
5. an alternative mechanism explains the effect equally well or better;
6. the effect fails independent replication.

## 13. External evidence

Existing empirical studies can provide secondary evidence and design benchmarks. They do not automatically satisfy this primary design because their escrow, trust, transparency, fulfilment, and outcome definitions may differ.

For example, recent research has directly examined escrow as a trust intermediary using large online transaction data, while newer technical work reports settlement/dispute outcomes under controlled experimental workloads. These are useful comparators but cannot be treated as direct validation of DEETI without passing the source gate.

## 14. R1 gate

R1 experimental-design readiness requires:

```text
ObservationUnitFrozen
∧ TreatmentDefined
∧ ControlDefined
∧ AssignmentRuleFrozen
∧ O1Frozen
∧ ETI_O1_SeparationVerified
∧ PrimaryEstimandFrozen
∧ PracticalEffectFrozen
∧ AlphaFrozen
∧ PowerRuleFrozen
∧ MissingnessRuleFrozen
∧ LeakageControlsFrozen
∧ ProvenancePlanFrozen
```

Until all predicates are satisfied, scientific status remains R0.
