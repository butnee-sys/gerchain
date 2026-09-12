# SHUUD 90-Day Sandbox — Day-0 Kickoff Baseline

## 1. Purpose

This document defines the Day-0 package for placing the verified SHUUD lifecycle into a controlled sandbox environment.

The sandbox validates operational performance in real conditions. The 2-minute objective is an operational benchmark to be tested, not a pre-validated field result.

## 2. Sandbox scope

### Included
- Minor road incidents eligible for rapid processing.
- Valid insurance coverage.
- No serious injury.
- No active dispute between involved parties.
- No immediate fraud or evidence-integrity red flag.
- Eligible vehicle/property damage within the sandbox compensation ceiling of MNT 2,000,000.
- Evidence capture, verification, SHIID decision, clearance, escrow and settlement measurement.

### Excluded from the rapid path
- Serious injury or emergency medical response.
- Fatality.
- Material third-party property damage outside the sandbox rule set.
- Disputed liability requiring extended investigation.
- Suspected fraud or tampered evidence.
- Incidents outside the configured compensation limit.

Excluded cases remain routed to the responsible conventional process and are not counted as rapid-path failures.

## 3. Verified technical lifecycle

`Incident -> Evidence -> Verification -> SHIID decision -> Clearance -> Escrow -> Settlement -> Measurement`

Operational lifecycle:

`REPORTED -> VERIFIED -> DISPATCHED/ON_SCENE -> CLEARING -> CLEARED -> CLAIM_OPENED -> CLOSED`

GerChain remains the authoritative infrastructure layer.

- WitnessChain remains the single authoritative witness chain.
- EscrowEngine remains the authoritative escrow transition engine.
- SHUUD persistence is a durability adapter and does not create a second state authority.
- Monetary semantics remain `amount_mnt`, `currency=MNT`, `settlement_provider=NEF`.

## 4. Day-0 participants and responsibilities

| Participant | Day-0 responsibility |
|---|---|
| City/road operations | Sandbox operational owner; road-clearance coordination |
| Insurer | Policy/claim confirmation; compensation authorization |
| SHUUD operator | Incident intake, verification workflow, exception routing |
| GerChain technical operator | Runtime, PostgreSQL, audit, persistence, recovery |
| Settlement/NEF operator | Escrow/settlement pathway and reconciliation |
| Evidence/AI verification partner | Evidence classification and verification support |
| Governance owner | Rules, eligibility, escalation and day-90 decision |

## 5. Environment

Minimum Day-0 technical environment:

- GerChain API/core services.
- SHUUD API.
- PostgreSQL 16.
- Durable SHUUD persistence.
- WitnessChain and EscrowEngine from the verified main branch.
- Audit/event records.
- Measurement API.
- Operational timing and economic measurement.
- Isolated sandbox data and credentials.

Production credentials, real customer secrets, and unrestricted payment authorization must not be used in the initial sandbox.

## 6. Day-0 acceptance checklist

### Technical
- [ ] Main branch baseline deployed.
- [ ] PostgreSQL connectivity verified.
- [ ] SHUUD persistence health verified.
- [ ] Process-restart recovery smoke test verified.
- [ ] CAS release race protection verified by existing CI baseline.
- [ ] Measurement API reachable.
- [ ] Audit trail retained for each sandbox incident.

### Operational
- [ ] Participant roles named.
- [ ] Rapid-path eligibility rules approved.
- [ ] Escalation path approved.
- [ ] Evidence minimum defined.
- [ ] Clearance confirmation responsibility defined.
- [ ] Settlement authorization responsibility defined.

### Measurement
- [ ] Baseline time definition approved.
- [ ] Actual clearance time captured.
- [ ] Actual settlement time captured.
- [ ] Percentage within 120 seconds calculated.
- [ ] Time saved calculated.
- [ ] User/vehicle, insurer and public-road economic inputs recorded explicitly.
- [ ] False approval/rejection and exception counts recorded.
- [ ] Recovery and audit completeness recorded.

## 7. Test scenario set

### S1 — Standard eligible minor incident
Expected: complete rapid path; measure total clearance time.

### S2 — Slow evidence capture
Expected: identify evidence bottleneck and route timing contribution.

### S3 — Verification rejection
Expected: rapid path stops safely; incident remains auditable.

### S4 — SHIID rejection
Expected: no unauthorized release; conventional handling continues.

### S5 — Process restart before release
Expected: state recovers from PostgreSQL and release continues safely.

### S6 — Concurrent release attempt
Expected: exactly one durable state transition wins; stale writer is rejected.

### S7 — Settlement delay
Expected: clearance timing and settlement timing remain separately measurable.

### S8 — Out-of-scope incident
Expected: excluded from rapid KPI numerator/denominator and routed to conventional handling.

## 8. KPI baseline

Primary KPI:

`within_two_minutes = actual_clearance_seconds <= 120`

Additional KPIs:

- Median clearance seconds.
- P90 clearance seconds.
- Incident-to-clearance seconds.
- Clearance-to-settlement seconds.
- Share of eligible incidents completed within 120 seconds.
- Evidence rejection rate.
- SHIID rejection rate.
- Exception/escalation rate.
- Process-restart recovery success rate.
- CAS conflict rate.
- Audit completeness rate.
- Estimated time saved per incident.
- Aggregate time saved.
- Explicitly parameterized economic savings.

## 9. 90-day operating sequence

### Days 0–14 — Setup
Environment, roles, rules, dashboards, evidence procedures, simulation data.

### Days 15–30 — Controlled simulation
Repeated end-to-end scenarios with known test cases. Tune rules and identify bottlenecks.

### Days 31–60 — Limited live sandbox
Small eligible cohort with operational oversight and manual fallback.

### Days 61–75 — Expanded sandbox
Increase incident volume and participant coverage; monitor KPI stability.

### Days 76–90 — Evaluation
Freeze measurement window, compare baseline against observed performance, quantify operational/economic effects, and prepare scale recommendation.

## 10. Day-90 decision gate

Scale only when:

1. Reliability is demonstrated under repeated sandbox operation.
2. Audit/evidence integrity is complete.
3. No unresolved state-authority conflict exists.
4. Operational clearance performance is measured rather than assumed.
5. Economic benefits are calculated from observed data and explicit assumptions.
6. Governance, insurer and city operating responsibilities are accepted.

Otherwise, continue sandbox with a defined corrective action plan.

## 11. Important boundary

This baseline does not claim that SHUUD currently clears real incidents within two minutes. It establishes the environment and measurement framework required to determine that empirically.
