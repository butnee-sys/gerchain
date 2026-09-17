# DEETI R1 Generic Escrow Transaction Protocol v1

**Status:** PROVISIONAL DESIGN
**Scientific status:** R0 — Registered hypothesis

## Purpose

Define a minimal transaction environment in which the Escrow Trinity capability can be varied without changing the underlying economic task.

## Transaction actors

```text
P — Provider / seller
B — Buyer / counterparty
E — Escrow mechanism
V — Independent verifier
```

## Common transaction task

1. P offers a predefined digital good/service.
2. B initiates a transaction with a predefined value.
3. The transaction enters either control or ET treatment.
4. A predefined condition must be satisfied.
5. Evidence is recorded.
6. Settlement occurs only according to the declared rule.
7. The transaction closes as completed, failed, disputed, or refunded.

The economic task, transaction value range, participant eligibility, and completion condition must be equivalent across arms.

## Control arm

The control arm uses the baseline governed transaction process without the full Escrow Trinity treatment.

It must retain the minimum operational controls needed for a legitimate transaction, but must not receive the treatment's additional Trust/Transparency/Fulfilment capability bundle.

## ET treatment arm

The treatment arm adds the pre-specified Escrow Trinity capability:

```text
TRUST
  +
TRANSPARENCY
  +
TRIUMPH / VERIFIED FULFILMENT
```

Each component must have an operational definition and auditable event evidence.

## Required lifecycle events

```text
INITIATED
IDENTITY_VERIFIED
CONDITION_DECLARED
EVIDENCE_REGISTERED
CONDITION_VERIFIED
ESCROW_LOCKED
FULFILMENT_CONFIRMED
SETTLEMENT_RELEASED | REFUNDED
DISPUTE_OPENED | NONE
CLOSED
```

Events must be timestamped and immutable/versioned.

## Primary outcome

```text
O1 = completed initiated transactions / initiated transactions
```

Completion must be determined independently from ETI coding.

## Secondary outcomes

- settlement delay;
- failure rate;
- dispute rate;
- evidence completeness;
- verification time;
- direct transaction cost.

## Treatment integrity

A treatment observation is valid only when all pre-specified ET components are actually delivered.

A control observation is contaminated if it receives treatment functionality. Such observations are coded according to the pre-specified protocol and are not silently reassigned.

## Blinding / independent coding

Where participant blinding is impossible, O1 adjudication must be independent from the ETI implementation team. Coding rules must be frozen before outcome inspection.

## Falsification

The design does not assume that ET treatment improves O1. It permits:

- no effect;
- negative effect;
- positive effect;
- effect only in specific strata;
- effect explained by one component rather than the full Trinity.

## Freeze blockers

Before R1 closure, freeze:

- exact transaction domain;
- value range;
- eligibility rules;
- treatment implementation;
- control implementation;
- randomization/allocation rule;
- practical effect delta;
- alpha;
- power;
- sample-size method;
- missingness and censoring rules;
- independent adjudication procedure.

No confirmatory outcome analysis is permitted before these items are frozen.
