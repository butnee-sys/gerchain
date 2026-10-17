# DEETI R1 Primary Experiment Source Freeze v1

**Status:** PROVISIONAL — not scientifically frozen
**Scientific status:** R0 — Registered hypothesis

## 1. Decision

The primary empirical design should use a **researcher-governed prospective transaction experiment with real-stake or otherwise consequential settlement**, rather than attempting to retrofit an existing public dataset to the DEETI construct.

This is a design decision, not an empirical result.

## 2. Why this source class

The experiment can independently control:

- ET capability exposure;
- treatment assignment;
- transaction initiation;
- evidence visibility;
- condition verification;
- settlement execution;
- dispute/failure states;
- timestamps and provenance.

This creates the temporal ordering required for the primary estimand:

`ETI exposure -> transaction lifecycle -> O1 outcome`

## 3. Primary comparison

```text
Control:
  ordinary governed transaction process

Treatment:
  same transaction process + pre-specified Escrow Trinity capability
```

The underlying economic task must remain equivalent between groups.

The treatment must not be defined using the observed outcome.

## 4. Primary estimand

For binary transaction reliability:

`O1 = completed initiated transactions / initiated transactions`

Primary treatment effect:

`ATE = E(O1 | ET treatment) - E(O1 | control)`

The confirmatory analysis must pre-specify the estimator, confidence interval, alpha, practical effect threshold, and missing-data rule before outcome inspection.

## 5. Required transaction evidence

Each transaction episode must preserve, at minimum:

- unique transaction identifier;
- treatment assignment;
- initiation timestamp;
- Trust evidence;
- Transparency evidence;
- verified-fulfilment evidence;
- condition verification event;
- payment/escrow state;
- settlement or refund event;
- dispute/failure state;
- completion timestamp;
- audit/provenance record.

## 6. Independent O1 coding

O1 completion must be reconstructed from lifecycle evidence independently of ETI coding.

No ETI component may be defined as a proxy for completion itself.

## 7. Falsification requirements

The primary hypothesis is not supported if:

- the treatment effect is practically negligible under the frozen delta;
- the confidence interval is incompatible with the pre-specified effect claim;
- the result disappears under pre-specified robustness checks;
- an equally credible control explanation accounts for the observed effect;
- component ablation shows no necessary contribution where necessity was hypothesized;
- independent replication fails.

## 8. Freeze blockers

This document is **not final** until all of the following are frozen:

1. concrete transaction domain;
2. participant population;
3. real-stake/consequence mechanism;
4. treatment implementation;
5. control implementation;
6. practical effect delta;
7. alpha and target power;
8. sample-size method;
9. missingness/censoring rules;
10. independent verification procedure;
11. provenance and data-access arrangements.

## 9. Scientific status

No claim of validation is made by this document. The protocol remains at R0 until the empirical source and all R1 gates are actually frozen and satisfied.
