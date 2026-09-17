# DEETI R1 Real Source Candidate v1

**Status:** Candidate design — not frozen
**Scientific status:** R0

## Candidate source class

The strongest current candidate is a **prospective controlled transaction-episode dataset generated in a real digital economic service environment** where the transaction lifecycle can be instrumented from initiation through final settlement or dispute closure.

This is preferred over retrofitting an existing public dataset because current public sources generally do not jointly expose the complete ETI construct and an independently coded O1 outcome.

## Required transaction lifecycle

```text
Initiated
  ↓
Identity / authority verified
  ↓
Terms visible
  ↓
Condition verified
  ↓
Escrow locked
  ↓
Delivery / obligation fulfilled
  ↓
Settlement OR dispute
  ↓
Closure
```

## Treatment

ET treatment must expose the pre-specified Escrow Trinity capability without changing the underlying economic task:

- Trust: verified authority/counterparty and protected conditional execution;
- Transparency: complete, time-stamped, independently inspectable evidence;
- Triumph: verified fulfilment leading to correct conditional settlement.

The treatment must not be defined using the observed O1 result.

## Control

The control must perform the same economic task with the ET capability removed or materially reduced according to a pre-specified rule, while preserving all other feasible conditions.

## Primary outcome

```text
O1 = completed initiated transactions / initiated transactions
```

Completion is independently coded under the frozen O1 coding protocol.

## Secondary outcomes

- dispute rate;
- settlement delay;
- direct transaction cost;
- evidence completeness;
- conditional settlement accuracy.

## Scientific caution

Existing literature supports studying escrow, transparency, trust, settlement and dispute outcomes separately or in combinations. For example, experimental evidence has found settlement escrows can affect settlement rates under asymmetric information, while recent transaction-framework research reports settlement and dispute metrics under controlled workloads. These are methodological precedents, not validation of DEETI.

## Candidate-source decision

```text
PRIMARY_ELIGIBLE: PROVISIONAL
Frozen source: NO
Confirmatory outcome inspected before selection: NO
```

## R1 blocker

The actual service environment, population, treatment implementation, sampling frame, practical effect threshold, alpha, power and sample size remain to be frozen before confirmatory data collection.
