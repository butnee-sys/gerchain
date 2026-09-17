# DEETI R1 — Generic Escrow Economic Consequence Source Map v1

**Status:** PROVISIONAL — R0/R1 preparation only  
**Research branch:** `research/deeti-economic-consequence-v1`  
**Purpose:** identify admissible evidence for estimating the economic consequence terms needed before freezing the practical-effect threshold δ.

## 1. Research question

For the pre-specified generic digital escrow/payment transaction environment, what independently traceable evidence can quantify:

- probability of transaction failure or non-completion;
- direct economic loss from failure;
- delay and time-value consequences;
- dispute and recovery costs;
- opportunity costs caused by unresolved or delayed settlement;
- incremental cost of implementing the Escrow Trinity treatment?

No confirmatory outcome data may be inspected for the purpose of choosing δ.

## 2. Source hierarchy

### Tier A — primary empirical evidence

Preferred:

1. transaction-level operational records from a real escrow/payment environment;
2. independently audited dispute and settlement records;
3. prospective transaction experiment records with real or consequential economic stakes;
4. regulator, court, or independently verified institutional records containing transaction/dispute costs.

### Tier B — high-quality external empirical evidence

Acceptable for prior calibration or external benchmarking:

- peer-reviewed experimental studies;
- peer-reviewed field/econometric studies;
- independently documented marketplace/payment statistics.

### Tier C — institutional descriptive evidence

Useful for defining cost categories and operational ranges, but not sufficient alone for causal estimation:

- documented escrow dispute procedures;
- published service-level timelines;
- institutional fee schedules;
- official marketplace or payment-system documentation.

### Tier D — illustrative/commercial sources

May identify candidate variables but cannot freeze δ without independent corroboration:

- vendor claims;
- product marketing material;
- simulations without real transaction consequences;
- uncited industry estimates.

## 3. Evidence already located

### 3.1 Babcock & Landeo (2004)

`Settlement escrows: an experimental study of a bilateral bargaining game`, Journal of Economic Behavior & Organization 53(3), 401–417.

This is a strong methodological precedent. The experiment found higher settlement rates and lower litigation costs when settlement escrow was introduced under asymmetric information, while the effect was absent under certainty. This establishes context dependence, not a universal escrow effect. It can therefore inform design and falsification but must not be used as the DEETI δ itself.

### 3.2 Online escrow adoption experiment

A 2006 experimental study of C2C online auction escrow adoption used 95 subjects and 80 transactions per subject and examined price, seller reputation, fraud rate and adoption decisions. This is useful for identifying behavioral and transaction-level variables, but adoption is not the DEETI primary outcome O1 and therefore it is not direct evidence for the foundational capability claim.

### 3.3 OECD marketplace evidence

OECD material documents marketplace practices in which payment can be released after receipt and complaints can pause payment and trigger mediation. Reported dispute-resolution response times varied from 1–2 days to several weeks across marketplaces. This is useful for defining delay/dispute consequence variables, but it is not a controlled causal estimate of DEETI.

### 3.4 Escrow.com published dispute process

Escrow.com documents a 14-day negotiation period followed by a 14-day arbitration commencement period in its dispute process. This is useful for defining observable delay states and potential opportunity-cost exposure, but provider documentation is Tier C rather than causal evidence.

## 4. Candidate cost model

For observation i:

`C_failure_i = direct_loss_i + delay_cost_i + dispute_cost_i + recovery_cost_i + opportunity_cost_i`

Only non-overlapping components may be summed.

For a candidate source s:

`E(C_failure | s) = Σ_k P(k | s) × C(k | s)`

where k is a mutually exclusive terminal consequence class.

Treatment cost:

`C_ET = implementation + verification + evidence + settlement + administration`

The economic decision threshold must satisfy:

`δ_economic × E(C_failure) >= E(C_ET)`

This is a decision-relevance condition, not a statistical significance condition.

## 5. Source acceptance rules

A source may contribute to δ only if:

`Provenance ∧ DefinitionStability ∧ TimeAlignment ∧ CostReconstructability ∧ NonOverlap`

are all satisfied.

A source is excluded from confirmatory δ selection when:

- the outcome is selectively reported;
- cost definitions are materially ambiguous;
- transaction population is unknown;
- treatment exposure is mixed with outcome definition;
- costs are marketing estimates without underlying records;
- simulated values are presented as real-world costs;
- the same loss is counted in more than one cost component.

## 6. Important methodological separation

Historical escrow studies demonstrate that escrow can affect transaction/settlement outcomes under particular conditions. They do **not** establish that Escrow Trinity is a universal foundational capability of Digital Economy.

The DEETI claim remains falsifiable:

`ET capability -> improved O1 reliability under a declared transaction environment`

and must survive controls, ablation, robustness testing and independent replication.

## 7. Current decision

No existing external source is currently sufficient by itself to freeze δ.

The preferred next source is a real, transaction-level, auditable escrow/payment dataset or a prospective controlled transaction environment in which:

- initiation is observable;
- terminal completion is independently observable;
- failure/dispute states are recorded;
- settlement delay is timestamped;
- economic value is known;
- direct and recovery costs are reconstructable;
- treatment cost can be measured independently.

## 8. R1 gate contribution

This artifact establishes the evidence-selection rule but does not satisfy the full R1 gate.

Remaining blockers:

1. concrete real transaction environment;
2. eligible source acquisition;
3. pre-outcome δ justification;
4. alpha/power/sample-size freeze;
5. independent O1 coding validation;
6. complete provenance and reproducibility package.

**Status remains: R0 / R1 preparation — NOT GREEN.**
