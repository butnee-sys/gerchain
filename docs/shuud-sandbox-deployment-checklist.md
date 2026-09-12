# SHUUD Sandbox Deployment Checklist

## Deployment objective
Deploy the verified GerChain + SHUUD baseline into an isolated sandbox and prove the environment is ready before any live operational trial.

## A. Infrastructure

- PostgreSQL 16 reachable from application runtime.
- SHUUD persistence points to the sandbox database.
- Database is isolated from production data.
- Runtime configuration is reproducible from documented environment variables.
- Application health endpoint and API documentation are reachable.

## B. Data and audit

- Sandbox incidents use synthetic or explicitly authorized test data.
- Every incident receives a unique incident identifier.
- Evidence records are retained.
- Verification and SHIID decisions are auditable.
- Escrow transitions are auditable.
- Measurement summary is retrievable after completion.

## C. Recovery and concurrency

- Process restart recovery test passes.
- Concurrent release CAS protection is active.
- A stale writer cannot overwrite the winning release state.
- No second WitnessChain is created.
- No second EscrowEngine is created.

## D. Operational rules

Rapid-path eligibility is limited to:

- valid insurance;
- no serious injury or fatality;
- no unresolved dispute;
- no fraud/evidence-integrity red flag;
- compensation within MNT 2,000,000;
- incident suitable for rapid clearance.

All excluded incidents must have an auditable escalation path.

## E. Measurement setup

Required fields:

- incident_created_at
- evidence_locked_at
- verification_completed_at
- shiid_decided_at
- clearance_confirmed_at
- settlement_released_at
- baseline_seconds
- actual_clearance_seconds
- actual_settlement_seconds
- within_two_minutes
- affected_vehicles
- vehicle_value_per_minute_mnt
- insurer_cost_per_minute_mnt
- public_road_cost_per_minute_mnt
- time_saved_seconds
- total_savings_mnt

Monetary assumptions must be sandbox inputs, not hard-coded facts.

## F. Day-0 smoke scenarios

1. Eligible incident completes the full rapid path.
2. Verification rejects an incident.
3. SHIID rejects an incident.
4. Process restarts while escrow is LOCKED.
5. Two concurrent release attempts occur.
6. Settlement completes after clearance.
7. An out-of-scope incident is escalated.

## G. Exit criteria

Sandbox deployment is ready for controlled participant testing when:

- all infrastructure checks pass;
- all smoke scenarios pass;
- audit trail is complete;
- measurement data is queryable;
- manual fallback is documented;
- participant roles and escalation contacts are assigned.

The 120-second target is a measurement objective. It must not be reported as field-proven until the sandbox produces observed evidence.
