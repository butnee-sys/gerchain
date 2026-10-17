# DEETI R1 Real Transaction Domain Selection v1

**Status:** PROVISIONAL — NOT FROZEN
**Scientific stage:** R0 → R1 preparation

## 1. Objective

Select a concrete real-stake digital economic transaction class for the first confirmatory DEETI experiment without selecting the domain because of favorable observed outcomes.

## 2. Required properties

The primary domain must satisfy all of the following before R1 freeze:

`RealStake ∧ RepeatableTransaction ∧ ETManipulable ∧ O1Observable ∧ TemporalOrdering ∧ IndependentVerification ∧ EconomicConsequence ∧ Provenance`

Where:

- **RealStake:** the transaction has real monetary value or a consequential resource commitment.
- **RepeatableTransaction:** materially similar transaction episodes can be observed repeatedly.
- **ETManipulable:** Trust, Transparency, and Verified Fulfilment can be deliberately implemented as a treatment capability.
- **O1Observable:** initiation and completion can be independently coded.
- **TemporalOrdering:** treatment exposure is determined before the primary outcome is realized.
- **IndependentVerification:** O1 can be verified without relying on the treatment provider's own declaration.
- **EconomicConsequence:** failure, delay, dispute, or successful completion has measurable economic consequences.
- **Provenance:** transaction evidence can be independently traced and reproduced.

## 3. Candidate classes

### Candidate A — Generic digital escrow/payment transaction

A buyer and provider exchange a defined digital or digitally mediated good/service under a pre-specified completion condition. Funds are locked before fulfilment and released/refunded according to verified conditions.

**Current suitability:** PRIMARY CANDIDATE.

Reason: cleanest separation between ET capability and the underlying economic task; suitable for randomized treatment/control design.

### Candidate B — Digital service delivery transaction

A defined service is ordered, evidence of fulfilment is generated, and payment is released conditionally.

**Current suitability:** SECONDARY CANDIDATE.

Main risk: outcome quality may become domain-specific unless the completion condition is sharply defined.

### Candidate C — SHUUD/SHIID minor-incident transaction

Insurance-linked minor road-incident resolution with escrow/payment and verified evidence.

**Current suitability:** LATER REPLICATION / APPLICATION DOMAIN.

Reason for exclusion from first foundational test: road, insurance, operator, AI verification, user behavior, and traffic conditions create additional causal pathways.

### Candidate D — Synthetic/framework workload

Simulated transactions or dataset-derived workloads.

**Current suitability:** EXPLORATORY / ENGINEERING VALIDATION ONLY.

They may test implementation mechanics but cannot by themselves establish a real-world foundational economic capability.

## 4. Primary domain decision rule

The first confirmatory domain should be selected by structural suitability, not by favorable outcome magnitude.

The selection record must be completed before inspecting confirmatory O1 results.

## 5. Current provisional decision

**Generic digital escrow/payment transaction** is provisionally selected as the first experimental domain class.

This is a design decision, not an empirical conclusion.

The experiment should use the same underlying economic task in both arms:

```text
CONTROL
same task + ordinary transaction process

ET TREATMENT
same task + Trust + Transparency + Verified Fulfilment
```

The primary estimand remains the treatment effect on O1:

`ATE = E[O1 | ET] - E[O1 | Control]`

ETI remains a secondary construct measurement:

`ETI = (T + Transparency + VerifiedFulfilment) / 3`

## 6. R1 freeze blockers

The domain is not frozen until the following are specified:

1. exact transaction type;
2. participant eligibility;
3. transaction value/consequence range;
4. completion condition;
5. treatment implementation;
6. control implementation;
7. independent O1 coding;
8. failure/dispute/censoring rules;
9. economic consequence measurement;
10. practical effect threshold δ;
11. alpha, power and sample-size method;
12. provenance and independent audit procedure.

## 7. Falsification relevance

The domain must permit the claim to fail. A domain that mechanically guarantees completion, mechanically enforces settlement, or prevents observation of failures is unsuitable for the foundational test.

A null or negligible treatment effect remains a valid scientific result.
