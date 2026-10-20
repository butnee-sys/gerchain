# DEETI R1 Primary Experimental Design v2

**Status:** PROVISIONAL — NOT FROZEN
**Scientific status:** R0

## 1. Purpose

Translate the DEETI foundational-capability hypothesis into a minimal controlled experiment that can be falsified without relying on retrospective outcome selection.

## 2. Experimental question

For the same underlying digital economic transaction, does adding a pre-specified Escrow Trinity capability — Trust, Transparency, and Verified Fulfilment — change transaction reliability relative to the baseline control process?

## 3. Unit of observation

One transaction episode.

Each episode must have:

- unique transaction identifier;
- provider and counterparty identifiers or pseudonyms;
- defined economic object/service;
- declared value;
- declared completion condition;
- treatment assignment before outcome;
- complete lifecycle timestamps;
- independently reconstructable terminal state.

## 4. Experimental arms

### Control

Baseline governed digital transaction process.

### Treatment

The same baseline process plus the frozen ET capability bundle.

```text
Control = Baseline
Treatment = Baseline + ET
```

No other material transaction rule may differ between arms.

## 5. Preferred allocation

Primary design: randomized assignment at the transaction-episode level, subject to feasibility and ethics.

If randomization is impossible, the protocol must move down the registered hierarchy:

1. credible quasi-experiment;
2. prospective matched assignment;
3. longitudinal comparison;
4. cross-sectional comparison.

Only the first design supports a straightforward experimental ATE interpretation.

## 6. Primary outcome

\[
O1_i = 1 \quad \text{if transaction } i \text{ satisfies the frozen completion rule}
\]

otherwise:

\[
O1_i = 0
\]

The aggregate primary endpoint is:

\[
O1 = \frac{\sum_i O1_i}{N_{initiated}}
\]

## 7. Primary estimand

For randomized assignment:

\[
ATE = E[O1_i(ET)] - E[O1_i(Control)]
\]

The primary statistical comparison is the treatment-control difference in completion probability.

## 8. Secondary outcomes

- settlement delay;
- verification time;
- failure probability;
- dispute probability;
- evidence completeness;
- direct transaction cost.

These cannot replace O1 as the primary endpoint after outcome inspection.

## 9. ETI measurement

\[
ETI_i = \frac{T_i + Tr_i + Tf_i}{3}
\]

ETI is a treatment-capability measurement and must be constructed independently of O1.

The primary randomized comparison is treatment assignment → O1. ETI intensity/component analysis is secondary unless separately pre-registered.

## 10. Blinding and independent adjudication

Where participant blinding is impossible, the person or process determining O1 must be independent of treatment implementation.

Automated coding is preferred where deterministic rules can be implemented. Human coding requires inter-rater validation.

## 11. Practical effect

Before confirmatory observations are inspected, define a minimum practically meaningful absolute improvement:

\[
\delta = O1_{ET} - O1_{Control}
\]

The selected \(\delta\) must have an external operational or economic justification. It cannot be selected after observing the treatment result.

## 12. Statistical decision

Default two-sided significance level:

\[
\alpha = 0.05
\]

Default planning power:

\[
1-\beta = 0.80
\]

These remain provisional until the domain, baseline rate, clustering structure, and real transaction volume are frozen.

## 13. Falsification

The foundational-capability hypothesis is not supported if the pre-specified analysis shows any of the following:

- treatment effect is practically negligible under frozen \(\delta\);
- confidence interval is incompatible with the pre-specified beneficial-effect region;
- treatment effect is not robust to registered sensitivity analyses;
- ETI/O1 separation fails;
- contamination invalidates the treatment-control contrast;
- independent adjudication cannot reproduce O1;
- a credible alternative mechanism explains the observed difference equally well or better.

## 14. Replication path

After a valid internal experiment:

```text
R0 hypothesis
   ↓
R1 design + measurement freeze
   ↓
R2 internal experiment
   ↓
R3 independent replication
   ↓
R4 prospective / out-of-sample validation
   ↓
R5 cross-domain validation
```

R2 alone must not be described as proof of a universal DE foundation.

## 15. Current blockers

The following must still be frozen before R1:

- concrete transaction domain;
- participant population;
- transaction value range;
- treatment implementation;
- control implementation;
- feasible allocation method;
- baseline O1 estimate;
- practical \(\delta\) justification;
- sample size / power calculation using the actual design;
- missingness and censoring rules;
- independent verification arrangement;
- source/provenance mechanism.

**Current status: R0 / PROVISIONAL.**
