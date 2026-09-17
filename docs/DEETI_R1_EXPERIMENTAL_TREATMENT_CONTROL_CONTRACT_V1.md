# DEETI R1 Experimental Treatment–Control Contract v1

**Status:** PROVISIONAL — NOT FROZEN
**Scientific status:** R0

## Purpose

Prevent treatment/control contamination and make the foundational-capability test falsifiable before real observations are inspected.

## 1. Common transaction

Both arms must perform the same underlying economic task:

- same transaction object/service definition;
- same eligibility criteria;
- same value range;
- same completion condition;
- same terminal-state definitions;
- same observation window;
- same independent O1 coding.

## 2. Control arm

Control receives the minimum baseline transaction process required for legitimate execution.

It may use ordinary identity, recordkeeping, payment and dispute procedures required by the selected domain.

It must not receive the additional bundled ET capability being tested.

## 3. Treatment arm

Treatment receives the same baseline process plus the pre-specified Escrow Trinity capability:

### Trust

The mechanism must provide the declared assurance that only authorized parties/actions can participate in or alter the transaction.

### Transparency

The mechanism must expose the pre-specified transaction conditions, evidence/provenance, and state transitions needed for independent verification.

### Triumph / verified fulfilment

The mechanism must verify the declared condition and execute the corresponding settlement/refund rule correctly.

## 4. Treatment fidelity

For each treatment observation, record binary/graded evidence that each component was actually delivered.

```text
Treatment eligible = TrustDelivered ∧ TransparencyDelivered ∧ FulfilmentVerified
```

A failed component is not silently imputed as delivered.

## 5. Contamination

Record any treatment capability received by a control observation and any missing ET capability in a treatment observation.

Primary analysis must follow the pre-specified allocation principle. Sensitivity analyses may report per-protocol results, but cannot replace the primary analysis after outcome inspection.

## 6. Allocation

Preferred order:

1. randomized assignment;
2. credible quasi-experimental assignment;
3. prospective matched assignment;
4. longitudinal comparison;
5. cross-sectional comparison.

Causal language is restricted to designs that support a credible counterfactual.

## 7. Primary estimand

For randomized treatment/control assignment:

\[
ATE = E[O1(ET)] - E[O1(Control)]
\]

where `O1` is independently coded transaction completion.

For non-randomized designs, the estimand and causal assumptions must be explicitly stated and the result must not automatically be called causal.

## 8. Falsification conditions

The foundational-capability hypothesis is not supported if, under the frozen design:

- ET has no practically meaningful effect on O1;
- the estimated effect is compatible with the null under the pre-specified decision rule;
- the effect disappears under pre-specified robustness checks;
- treatment fidelity is insufficient;
- control contamination invalidates the contrast;
- ETI/O1 separation fails;
- an alternative explanation accounts for the result equally well or better;
- independent replication fails.

## 9. Freeze rule

No treatment/control implementation may be modified after confirmatory outcome inspection.

Before R1 closure, freeze:

`Domain ∧ Population ∧ ValueRange ∧ Treatment ∧ Control ∧ Allocation ∧ O1Coding ∧ δ ∧ Alpha ∧ Power ∧ SampleSize ∧ Missingness ∧ Provenance`.

Current state: **R0 / PROVISIONAL**.
