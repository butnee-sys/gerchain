# DEETI R1 Transaction Consequence Evidence Ledger v1

**Status:** PROVISIONAL — R0/R1 preparation; NOT FROZEN

## 1. Purpose

This ledger defines how empirical evidence will be recorded before a practical-effect threshold (`δ`) for the DEETI foundational-capability test is frozen.

The purpose is not to prove that escrow is beneficial in general. The purpose is to establish whether a concrete, economically meaningful improvement in transaction reliability can be specified **before confirmatory outcome inspection**.

## 2. Primary research environment

The initial research environment is a **generic digital marketplace escrow transaction**:

- buyer and seller;
- one identifiable transaction episode;
- declared transaction value;
- pre-specified fulfilment condition;
- conditional/escrow settlement;
- independently observable terminal state.

This is a research environment, not a claim about any particular marketplace.

SHUUD/SHIID remains a later replication/application domain and is not used to define `δ` for the foundational test.

## 3. Evidence chain

For every candidate empirical source, record:

`Source → Transaction consequence → Economic quantity → Unit → Transformation → Uncertainty → δ relevance`

No value enters the confirmatory analysis without a traceable chain.

## 4. Consequence categories

| Code | Consequence | Minimum observable quantity |
|---|---|---|
| C1 | Failed/non-completed transaction | failure frequency and direct loss |
| C2 | Settlement delay | delay duration and cost per unit time |
| C3 | Dispute | dispute frequency and resolution burden |
| C4 | Recovery/refund | recovery cost and time |
| C5 | Opportunity cost | measurable lost productive/economic activity |
| C6 | DEETI operating cost | implementation, verification, settlement and operating cost |

A source may populate one or more categories, but overlapping costs must not be counted twice.

## 5. Evidence hierarchy

### Tier A — transaction-level primary evidence

Preferred:

- transaction records;
- escrow/payment event logs;
- dispute and recovery records;
- independently audited operational records;
- prospective experimental observations.

### Tier B — independent empirical research

Peer-reviewed experimental or observational studies may establish effect direction, plausible consequence magnitudes, or design parameters.

The 2004 settlement-escrow experiment is a **design precedent**, not direct DEETI validation. It found higher settlement rates and lower litigation costs when settlement escrow was added under asymmetric information, while finding no escrow effect under certainty. This conditionality is important for falsification. 

### Tier C — institutional operational evidence

Examples include documented marketplace payment-release rules, complaint windows, mediation procedures, and observed resolution times. OECD evidence reports marketplace complaint-resolution times ranging from approximately 1–2 days to several weeks and describes payment being released after receipt in some marketplace systems. These observations are contextual unless transaction-level denominators and consequences are available.

### Tier D — secondary/commercial estimates

Commercial fee pages, vendor claims, blogs and illustrative estimates may be used only for hypothesis formation or sensitivity ranges. They cannot independently freeze `δ`.

## 6. Evidence ledger fields

Each candidate observation must contain:

- `evidence_id`
- `source_id`
- `source_type`
- `source_version_or_date`
- `transaction_domain`
- `jurisdiction`
- `observation_period`
- `transaction_unit`
- `transaction_value`
- `consequence_code`
- `frequency_or_probability`
- `duration`
- `unit_cost`
- `total_cost`
- `currency`
- `price_year`
- `inflation_conversion_method`
- `uncertainty_or_interval`
- `extraction_method`
- `coding_version`
- `transformation_version`
- `independent_verification`
- `double_counting_check`
- `delta_relevance`
- `outcome_inspected_before_recording`
- `notes`

## 7. Economic consequence calculation

For mutually exclusive failure modes `j`:

`E(C_F) = Σ_j P(F_j) × C(F_j)`

where:

- `P(F_j)` = probability/frequency of failure mode `j`;
- `C(F_j)` = economic consequence of that failure mode.

DEETI operating cost must be kept separate:

`E(C_ET) = C_implementation + C_operation + C_verification + C_settlement`

The decision-relevant economic benefit is conceptually:

`AvoidedConsequence − AdditionalDEETICost`

No benefit estimate may include a cost already included elsewhere in the ledger.

## 8. Relation to practical δ

The practical threshold must satisfy both:

`EconomicMeaning ∧ OperationalMeaning ∧ PreOutcomeSpecification`

Therefore `δ` cannot be selected because:

- a statistical result is significant;
- the available sample makes a particular `δ` convenient;
- a prior escrow study reported a large effect;
- a synthetic simulation produces a large effect;
- a commercial provider claims a percentage improvement.

A defensible `δ` is the smallest improvement in O1 that produces a pre-specified, decision-relevant economic consequence in the chosen environment.

## 9. Current external evidence interpretation

The 2004 controlled settlement-escrow experiment provides evidence that an escrow institution can affect settlement outcomes under asymmetric information, including higher settlement rates and lower litigation costs. It does not identify a universal effect size for digital marketplace transactions and does not test the full Trust–Transparency–Verified Fulfilment bundle.

OECD marketplace evidence provides real-world examples of conditional payment release, complaint windows and mediation, including resolution-time variation from 1–2 days to several weeks. These observations support measurement of delay and dispute consequences but do not, by themselves, identify the causal effect of DEETI.

Accordingly, these sources should be treated as **parameter-design evidence**, not as confirmation of the foundational hypothesis.

## 10. Falsification conditions

The proposed foundational capability is weakened or rejected if:

1. no economically meaningful `δ` can be justified independently of confirmatory outcomes;
2. the cost of implementing the ET capability is greater than plausible avoided consequences;
3. the observed O1 improvement is consistently below the frozen `δ`;
4. the relationship disappears after legitimate pre-specified controls;
5. an alternative mechanism explains the improvement equally well or better;
6. removal of an ET component produces no meaningful degradation where component necessity is predicted;
7. independent replication fails.

## 11. Current gate status

| Gate | Status |
|---|---|
| Transaction environment defined | YES — provisional |
| Economic consequence variables defined | YES |
| Evidence hierarchy defined | YES |
| Non-double-counting rule defined | YES |
| External design precedent identified | YES |
| Transaction-level empirical values obtained | NO |
| ET implementation cost obtained | NO |
| Practical `δ` frozen | NO |
| Power/sample size frozen | NO |
| R1 GREEN | NO |

## 12. Next required action

The next empirical step is to obtain a **real transaction-level or independently audited dataset** containing at least:

`initiated transactions + completed transactions + transaction value + failure/dispute state + delay/recovery information + provenance`

and, separately, a defensible estimate of the incremental cost of the ET capability.

Only after those quantities are documented independently can `δ` be proposed for freeze.

---

**Important:** This document records a falsifiable research protocol. It is not evidence that DEETI is already a scientifically established foundational capability.
