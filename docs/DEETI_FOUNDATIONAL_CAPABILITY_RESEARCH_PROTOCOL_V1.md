# DEETI Foundational Capability Research Protocol v1

**Status:** RESEARCH PROTOCOL — NOT YET VALIDATED
**Version:** 1.0
**Date:** 2026-09-17
**Repository:** `butnee-sys/gerchain`

## 1. Research purpose

This protocol defines a falsifiable, measurable, and comparative test of the proposed relationship:

```text
ET = Escrow Trinity = Trust + Transparency + Triumph

ET  ───────────────►  DE foundational capability
```

The research question is:

> Does the Escrow Trinity constitute a foundational capability for Digital Economy activity, such that higher ET capability is associated with and/or causally contributes to more reliable, lower-friction, more verifiable digital economic transactions?

This is a research hypothesis, not an established scientific law. A scientific hypothesis must generate predictions that can be contradicted by evidence; reproducibility, robustness, and independent replication are also required for stronger credibility.

## 2. Conceptual definitions

### 2.1 DEETI

**DEETI = Digital Economy Escrow Trinity Infrastructure**

Монгол хэлээр: **Эскроу гурвалд суурилсан Дижитал эдийн засгийн дэд бүтэц.**

DEETI is the proposed infrastructure model that operationalizes the Escrow Trinity as a foundational capability of Digital Economy activity.

### 2.2 Escrow Trinity (ET)

For this protocol:

```text
ET = T + Tr + Tf
```

where:

- `T` = **Trust** — итгэлцэл;
- `Tr` = **Transparency** — ил тод, шалгагдах боломж;
- `Tf` = **Triumph**, operationalized as **verified fulfilment** — тохиролцсон нөхцөл биелсэн бөгөөд биелэлт нь нотлогдох боломж.

The use of verified fulfilment as the measurable definition of Triumph prevents Triumph from becoming a subjective success judgement.

### 2.3 Foundational capability

A capability is considered **foundational** only if removing or materially weakening ET produces a measurable deterioration in one or more pre-specified Digital Economy outcomes, while controlling for plausible alternative explanations.

Thus “foundational” is an empirical claim, not a rhetorical label.

## 3. Main hypothesis

### H1 — Foundational capability hypothesis

> Digital economic transaction environments with higher measurable ET capability exhibit superior transaction reliability and/or lower transaction friction than otherwise comparable environments with lower ET capability.

A stronger causal version is:

> Increasing ET capability causes measurable improvement in pre-specified Digital Economy outcomes, relative to an appropriate counterfactual or control condition.

### H0 — Null hypothesis

> After controlling for relevant confounders and baseline system characteristics, ET capability has no practically meaningful effect on the pre-specified Digital Economy outcomes.

### H2 — Component necessity hypothesis

Removing any one of Trust, Transparency, or verified Fulfilment materially weakens the combined capability.

### H3 — Complementarity hypothesis

The combined ET capability produces an effect greater than the independent contribution of any single component, after accounting for interaction effects.

## 4. Falsification conditions

The hypothesis must be treated as **not supported** if one or more of the following pre-specified results occur:

1. ET capability has no statistically or practically meaningful relationship with the primary outcome across adequately powered tests.
2. The relationship disappears after reasonable controls for transaction complexity, participant risk, institutional quality, technology maturity, and market structure.
3. A credible alternative model explains the observed outcome equally well or better without ET.
4. Removing one ET component produces no measurable degradation where H2 predicts degradation.
5. ET improves transparency/trust perceptions but does not improve actual transaction reliability or friction.
6. Results fail in independent datasets, domains, or jurisdictions.
7. Results are highly sensitive to reasonable changes in measurement, weighting, missing-data treatment, or model specification.

A positive association alone is therefore insufficient to establish the foundational claim.

## 5. Operational measurement model

### 5.1 ET capability index

The primary index should be constructed before outcome testing:

```text
ETI = wT·T + wTr·Tr + wTf·Tf
```

with:

```text
wT + wTr + wTf = 1
```

The primary specification should use equal weights unless a pre-registered empirical weighting procedure is justified. Alternative weighting schemes must be tested as robustness checks.

All components must be normalized to a common scale, preferably `[0,1]`.

### 5.2 Trust indicators

Candidate measurable indicators include identity/authority verification success, dispute incidence, counterparty trust score, unauthorized-action rate, verified-authority coverage, repeat participation attributable to trust, and failed authorization rate.

### 5.3 Transparency indicators

Candidate indicators include transaction-trace completeness, evidence availability, condition visibility, auditability, provenance completeness, decision explainability, and the proportion of material events with independently reconstructable evidence.

### 5.4 Triumph / verified fulfilment indicators

Candidate indicators include condition-fulfilment verification rate, successful conditional execution rate, settlement completion rate, failed fulfilment rate, unresolved conditional transactions, time from condition satisfaction to authorized completion, and post-settlement reversal/dispute rate.

## 6. Digital Economy outcome variables

The primary outcome must be selected before observing final results.

Candidate primary outcomes:

### O1 — Transaction reliability

```text
O1 = successfully completed governed transactions / initiated governed transactions
```

### O2 — Transaction friction

Measures may include transaction time, verification time, dispute-resolution time, settlement delay, administrative steps, and direct transaction cost.

### O3 — Failure rate

```text
O3 = failed or disputed transactions / total transactions
```

### O4 — Evidence integrity

```text
O4 = transactions with complete reconstructable evidence / total transactions
```

### O5 — Conditional settlement performance

```text
O5 = verified conditions followed by correct authorized settlement / eligible conditions
```

The primary endpoint should be selected from O1–O5 before confirmatory analysis. The remaining outcomes are secondary endpoints.

## 7. Comparative design

A comparative design is mandatory because the proposition concerns capability, not merely correlation.

### Comparison A — ET-enabled vs non-ET

Compare otherwise similar transaction environments with different levels of ET implementation.

### Comparison B — High vs low ET capability

Use continuous ETI rather than an arbitrary binary classification.

### Comparison C — Component ablation

Test:

```text
T + Tr + Tf
T + Tr
T + Tf
Tr + Tf
T only
Tr only
Tf only
```

This tests whether the three components are jointly necessary or merely correlated.

### Comparison D — Before vs after

Where a real system introduces an ET intervention, compare pre-intervention and post-intervention outcomes with an appropriate control group or interrupted-time-series design.

### Comparison E — Cross-domain replication

Test across materially different transaction domains, such as peer-to-peer digital transactions, insurance/escrow transactions, asset transactions, supply-chain transactions, and public-sector digital transactions.

## 8. Causal identification

Where observational data are used, association must not be presented as causation.

Preferred designs, in descending evidentiary strength:

1. randomized or controlled experiment;
2. quasi-experimental intervention;
3. difference-in-differences;
4. interrupted time series;
5. matched comparative design;
6. longitudinal observational analysis;
7. cross-sectional association.

The design must specify the estimand, treatment/exposure definition, counterfactual, covariates, exclusion criteria, and missing-data rules before confirmatory analysis.

## 9. Confounders and controls

At minimum, models should consider transaction value, transaction complexity, participant count, participant experience, institutional/regulatory environment, technology maturity, transaction volume, dispute exposure, identity-verification requirements, settlement mechanism, market concentration, time period, and jurisdiction/domain.

Controls must be selected based on a pre-specified causal model rather than chosen after observing the outcome.

## 10. Statistical analysis

The analysis plan should include effect size and confidence interval, appropriate hypothesis test, practical significance threshold, model diagnostics, heterogeneity analysis, sensitivity analysis, missing-data analysis, and multiple-testing control where applicable.

For continuous outcomes, regression or hierarchical models may be used. For binary outcomes, logistic or appropriate generalized linear models may be used. Time-to-event outcomes may use survival/time-to-event methods.

The statistical method must follow the data-generating process rather than being selected to obtain significance.

## 11. Robustness and stress testing

Re-analysis is required under reasonable alternatives:

- equal vs empirically estimated ET weights;
- alternative normalization methods;
- alternative definitions of verified fulfilment;
- alternative transaction-complexity controls;
- alternative time windows;
- exclusion/inclusion of influential observations;
- missing-data strategies;
- alternative model specifications;
- alternative domain subsets.

A result that exists only under one fragile specification must not be classified as robust.

## 12. Evidence levels

```text
R0 — Registered hypothesis
R1 — Operationalized measurement model
R2 — Internal empirical test
R3 — Independent replication
R4 — Prospective / out-of-sample validation
R5 — Cross-domain capability validation
```

**Current status: R0 — Registered hypothesis.**

No GREEN, validated, causal, universal-law, or scientifically established status is claimed by this document alone.

## 13. Reproducibility requirements

The research record must preserve:

- protocol version;
- hypothesis version;
- dataset versions/vintages;
- code commit SHA;
- environment/dependency lock;
- data dictionary;
- variable transformations;
- analysis scripts;
- model specifications;
- random seeds where applicable;
- raw and derived-data hashes where legally possible;
- complete result tables;
- negative results;
- deviations from protocol;
- independent replication records.

## 14. Current evidence status

Existing research provides relevant but **not sufficient** evidence for the proposed DEETI hypothesis. Empirical work in digital transaction environments links transparency and trust to platform participation, while data-trust research identifies transparency as important to governance and adoption. These findings motivate the hypothesis but do not establish that the Escrow Trinity is foundational to the entire Digital Economy.

Research on digital platforms also describes escrow as a mechanism for addressing trust problems between participants and as a central feature of some platform business models.

## 15. Research contribution claim

The intended scientific contribution is **not** the claim that trust, transparency, or escrow are individually new concepts.

The proposed contribution is the testable proposition that:

```text
Escrow Trinity
      ↓
foundational capability
      ↓
Digital Economy transaction reliability / verifiability / fulfilment
```

and, if supported by evidence, the resulting **DEETI infrastructure model** that operationalizes this relationship.

The claim becomes scientifically stronger only as it survives increasingly difficult falsification attempts, robustness tests, and independent replication.

## 16. Relation to the frozen GerChain architecture

This protocol does **not** replace or modify the frozen architecture in `docs/DEE_ARCHITECTURE_FREEZE.md`.

The frozen architecture remains authoritative for implementation. It currently defines G-3 as the escrow foundation and records an operational Escrow Trinity of Trust + Transparency + Performance. This protocol is a **research layer** for testing the broader DEETI proposition and currently uses **Triumph / verified fulfilment** as its measurement term.

Any future architectural adoption of DEETI must occur through the repository's explicit architecture-change governance process.

## 17. Required next empirical stage

The next stage is to construct a **DEETI Evidence Dataset v1** containing observations sufficient to calculate:

```text
ETI
O1
O2
O3
O4
O5
```

and to define at least one credible non-ET or lower-ET comparison group.

Only after the dataset, measurement code, and pre-specified analysis are available should the project advance from **R0** to **R1**.

---

**Scientific status:** Hypothesis registered; not yet validated.
