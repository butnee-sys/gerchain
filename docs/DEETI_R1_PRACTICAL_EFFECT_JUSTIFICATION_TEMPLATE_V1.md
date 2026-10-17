# DEETI R1 Practical Effect δ Justification Template v1

**Status:** R1 preparation — template only
**Scientific status:** R0

## 1. Purpose

The minimum practically meaningful effect `δ` for O1 must be justified independently of the observed confirmatory outcome.

## 2. Required justification

Before confirmatory data inspection, document:

1. baseline O1 expected from the eligible population;
2. operational consequence of a one-unit ETI increase;
3. economic/resource consequence of an absolute O1 change;
4. minimum improvement that would change a real operational decision;
5. source(s) supporting the baseline and consequence assumptions;
6. uncertainty range used in planning.

## 3. Recommended formulation

Let:

```text
p0 = pre-specified baseline completion probability
δ  = minimum practically meaningful absolute improvement
p1 = p0 + δ
```

The planning value of `δ` must not be chosen by maximizing statistical power or by selecting the smallest effect observed in the eventual dataset.

## 4. Decision-theoretic interpretation

A candidate `δ` should correspond to a change that is materially consequential for the studied transaction process, for example reduced failed transactions, reduced resource loss, reduced delay, or increased reliable completion.

The justification must identify the mechanism rather than merely state that a percentage “looks meaningful.”

## 5. Freeze record

```text
Baseline source:
Baseline period:
Population:
Candidate δ:
Operational consequence:
Economic consequence:
Planning uncertainty:
Date frozen:
Version:
```

## 6. Prohibition

No confirmatory result may be used to revise `δ` for the same dataset. A revised value creates a new exploratory specification and must be versioned separately.

## 7. Gate

```text
SubstantiveJustification
∧ BaselineDefined
∧ ConsequenceDefined
∧ DeltaFrozenBeforeOutcomeInspection
```

Only then can the practical-effect parameter enter the final power calculation.
