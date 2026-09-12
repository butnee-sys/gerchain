# SHUUD 90-Day Sandbox Technical Baseline

## 1. Purpose

This document defines the technical baseline for a 90-day SHUUD sandbox using the GerChain infrastructure already verified through PostgreSQL and end-to-end CI.

The sandbox objective is to validate an operational workflow for eligible minor road incidents with a target of clearing the roadway within 2 minutes, while measuring operational time saved and corresponding economic impact.

The 2-minute target is an operational benchmark to be validated in the sandbox. It is not a claim of field performance before measurement.

## 2. Verified technical baseline

The verified lifecycle is:

```text
Incident
  -> Evidence
  -> SHIID verification/decision
  -> Clearance
  -> Escrow LOCKED
  -> Release
  -> Measurement Summary
```

Persistence and resilience are verified through:

```text
PostgreSQL persistence
  -> process restart recovery
  -> release CAS protection
```

The authoritative state components remain:

- Existing `WitnessChain` is authoritative for witness/evidence history.
- Existing `EscrowEngine` is authoritative for escrow state transitions.
- `SHUUDPersistence` is a durable snapshot/recovery adapter, not a second state engine.
- MNT remains the monetary currency.
- NEF remains the settlement provider/infrastructure identifier.

No second WitnessChain and no second EscrowEngine are introduced by the SHUUD application layer.

## 3. Sandbox scope

### In scope

- Eligible minor road incidents.
- Two-party vehicle/property cases.
- Verified evidence and consent.
- Insurance-valid cases.
- Damage cases within the sandbox compensation ceiling.
- Operational timing from incident occurrence through clearance and settlement.
- Economic time-saved measurement for affected road users, insurer operations, and public-road operations.
- PostgreSQL durability and restart recovery.
- Concurrent release protection through compare-and-set persistence.

### Out of scope

- Serious injury or emergency medical response.
- Criminal investigations.
- Disputed liability adjudication.
- Third-party property damage requiring separate claims handling.
- Traffic-flow control as a municipal traffic-management system.
- Automatic approval outside the defined SHIID policy gates.

## 4. 90-day implementation phases

### Phase 1 — Days 1-15: controlled readiness

Objectives:

1. Freeze the verified GerChain/SHUUD technical baseline.
2. Establish sandbox operator roles and access.
3. Establish the PostgreSQL sandbox environment.
4. Confirm evidence, consent, verification, escrow and release operating procedures.
5. Capture baseline time measurements before optimization.

Deliverables:

- Sandbox operating procedure.
- Test incident catalogue.
- Operator access matrix.
- Baseline measurement sheet.
- Incident eligibility checklist.

Exit gate:

- Every readiness test passes in CI.
- No skipped readiness stage.
- Sandbox test incident can complete the full lifecycle.

### Phase 2 — Days 16-45: limited live-like operation

Objectives:

1. Run controlled sandbox cases.
2. Measure each operational milestone.
3. Identify delay sources.
4. Validate evidence and SHIID gate quality.
5. Validate escrow/release reliability.

Primary measurements:

- Incident -> evidence.
- Evidence -> verification.
- Verification -> SHIID.
- SHIID -> clearance.
- Clearance -> settlement.
- Incident -> clearance.
- Incident -> settlement.
- Share of eligible incidents within 120 seconds.
- Failed verification rate.
- Rejected eligibility rate.
- Escrow release failure rate.
- Persistence/recovery incidents.

Exit gate:

- Data captured for every sandbox case.
- No unresolved state-integrity failures.
- Operational bottlenecks documented.

### Phase 3 — Days 46-75: operational optimization

Objectives:

1. Reduce the largest measured delay sources.
2. Tune operator workflows.
3. Improve evidence collection quality.
4. Improve insurer and operations-center handoff.
5. Validate repeatability rather than isolated best-case performance.

Acceptance focus:

- Median clearance time.
- P90 clearance time.
- P95 clearance time.
- Within-120-second share.
- Settlement completion rate.
- Manual intervention rate.

No economic assumption is embedded in the software. Monetary values remain explicit sandbox inputs.

### Phase 4 — Days 76-90: evaluation and scale decision

Objectives:

1. Produce the final sandbox dataset.
2. Compare baseline vs SHUUD measured performance.
3. Quantify time saved and economic impact.
4. Document operational, technical and governance requirements for scale.
5. Prepare the municipal procurement/investment case.

Final deliverables:

- 90-day performance report.
- Economic impact report.
- Technical readiness report.
- Governance and operating model.
- Scale-up requirements.
- Budget and investment case.

## 5. Economic measurement model

For each eligible sandbox incident:

```text
saved_minutes = max(baseline_seconds - actual_clearance_seconds, 0) / 60

vehicle_user_savings
  = saved_minutes
  * affected_vehicles
  * vehicle_value_per_minute_mnt

insurer_savings
  = saved_minutes
  * insurer_cost_per_minute_mnt

public_road_savings
  = saved_minutes
  * public_road_cost_per_minute_mnt

total_savings
  = vehicle_user_savings
  + insurer_savings
  + public_road_savings
```

All monetary rates are sandbox inputs supported by evidence or an explicit assumption register. The measurement layer does not hard-code the economic value of time.

## 6. Sandbox governance

Minimum operating participants:

- SHUUD sandbox operator.
- Insurer representative.
- Road operations/rapid-response representative.
- Technical operator.
- Evidence/verification authority.
- Settlement/NEF representative where settlement is activated.

Every sandbox case must have an auditable incident identifier and a recoverable state snapshot.

## 7. Technical success criteria

The sandbox is considered technically successful when:

1. Full eligible lifecycle completes without manual database intervention.
2. PostgreSQL persistence remains recoverable across process restart.
3. Concurrent release attempts cannot produce two successful durable state writers.
4. Witness/evidence history remains authoritative through the existing WitnessChain.
5. Escrow transitions remain authoritative through the existing EscrowEngine.
6. MNT and NEF semantics remain separated.
7. Every completed incident produces operational timing data.
8. Economic measurement can be reproduced from stored measurements and explicit inputs.

## 8. Operational success criteria

The sandbox should report, rather than assume:

- median clearance time;
- P90 and P95 clearance time;
- percentage of eligible incidents cleared within 120 seconds;
- median settlement time;
- evidence completeness rate;
- verification approval rate;
- manual intervention rate;
- failed release rate;
- recovery incidents;
- measured economic savings per incident;
- aggregate measured economic savings.

The 120-second benchmark is a target metric. The sandbox report must preserve both successes and failures.

## 9. Scale decision at Day 90

At Day 90, the decision is based on measured evidence:

```text
Sandbox data
    -> technical readiness
    -> operational readiness
    -> economic value
    -> governance readiness
    -> scale / revise / stop decision
```

No production-scale claim should be made before this evidence set is complete.

## 10. Relationship to GerChain

GerChain remains the infrastructure layer.

SHUUD is the domain application using GerChain for evidence, verification, durable state, escrow coordination and measurement.

The sandbox therefore validates both:

```text
SHUUD application performance
        +
GerChain infrastructure reliability
```

This is the technical baseline for subsequent municipal sandbox, procurement, partnership and investment discussions.
