# DEETI R1 Actual Comparison Design v1

**Status:** R1 preparation — provisional design specification
**Scientific status:** R0
**Date:** 2026-09-17

## 1. Default empirical design

Until a stronger real-world intervention or credible quasi-experiment is identified, the first empirical test will use a **prospective controlled transaction-episode comparison**.

The unit is one transaction episode.

The exposure is the pre-specified ETI measurement available before the O1 observation window closes.

The primary outcome is O1 transaction reliability.

## 2. Comparison construction

The preferred analysis uses continuous ETI variation rather than an outcome-derived arbitrary high/low split.

Primary model:

```text
O1_i = f(ETI_i, Complexity_i, Value_i, Maturity_i,
         Domain_i, Jurisdiction_i, Period_i)
```

For a binary transaction-level outcome, the primary model must be a pre-specified binary-outcome model. For grouped rates, a binomial model is preferred.

A high/low ETI comparison may be used only as a secondary interpretive analysis with a threshold frozen before outcome inspection.

## 3. Counterfactual requirement

A simple continuous association is not automatically causal.

Causal language requires a credible intervention or quasi-experimental identification strategy. Otherwise the primary conclusion is restricted to association.

## 4. Confounding controls

The minimum planned controls are:

- transaction value;
- transaction complexity;
- technology/process maturity;
- domain;
- jurisdiction/institutional environment;
- period;
- participant/counterparty exposure where measurable;
- transaction volume where relevant.

Controls are not to be added selectively after observing the O1 result.

## 5. Exposure timing

The ETI measurement used for the primary analysis must be defined from information available before the O1 outcome window closes.

Post-outcome information is prohibited from entering the primary ETI construction.

## 6. Primary estimand

The primary estimand is the pre-specified change in the probability of O1 completion associated with a one-unit increase in ETI on the [0,1] scale, conditional on the declared design and covariates.

For observational data, this is an association estimand. It becomes a causal estimand only if the identification assumptions of the selected intervention/quasi-experimental design are justified.

## 7. Design upgrade rule

If an eligible real-world source provides:

```text
randomized exposure
OR
credible exogenous exposure
OR
credible natural experiment
```

before confirmatory outcome inspection, the study design must be upgraded and the analysis plan versioned accordingly.

## 8. Design rejection conditions

The provisional design must not be used if:

- ETI exposure is assigned using final O1;
- no meaningful ETI variation exists;
- comparison membership is outcome-dependent;
- O1 cannot be independently reconstructed;
- material confounding cannot be measured or bounded;
- transaction episodes are not independently identifiable.

## 9. Freeze condition

This document becomes the empirical design freeze only after the actual source, population, period, exposure assignment, and sample-size/power calculation are attached to a versioned study record before confirmatory outcome inspection.
