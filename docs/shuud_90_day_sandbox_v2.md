# SHUUD 90-Day Sandbox Technical Baseline

This document defines the technical baseline for the 90-day SHUUD sandbox after the GerChain PostgreSQL/SHUUD readiness gate passed.

## Phases

- Days 1-15: controlled readiness, roles, access, PostgreSQL environment, operating procedure, eligibility checklist, baseline timing.
- Days 16-45: controlled live-like operation, milestone timing, evidence/verification quality, escrow/release reliability.
- Days 46-75: optimize measured delay sources and validate repeatability using median/P90/P95 clearance time, within-120-second share and manual intervention rate.
- Days 76-90: final performance, economic, technical and governance reports plus scale/procurement/investment decision.

## Verified lifecycle

```text
Incident -> Evidence -> SHIID -> Clearance -> Escrow LOCKED -> Release -> Measurement Summary
```

## Architecture invariants

- Existing WitnessChain remains authoritative for witness/evidence history.
- Existing EscrowEngine remains authoritative for escrow state transitions.
- SHUUDPersistence is durable snapshot/recovery only, not a second state engine.
- MNT is the monetary currency.
- NEF is the settlement provider/infrastructure identifier.
- No second WitnessChain or second EscrowEngine is introduced.

## Economic measurement

```text
saved_minutes = max(baseline_seconds - actual_clearance_seconds, 0) / 60
vehicle_user_savings = saved_minutes * affected_vehicles * vehicle_value_per_minute_mnt
insurer_savings = saved_minutes * insurer_cost_per_minute_mnt
public_road_savings = saved_minutes * public_road_cost_per_minute_mnt
total_savings = vehicle_user_savings + insurer_savings + public_road_savings
```

Monetary rates remain explicit sandbox inputs and must be supported by evidence or an assumption register.

## Day-90 decision

```text
Sandbox data -> technical readiness -> operational readiness -> economic value -> governance readiness -> scale / revise / stop
```

The 120-second target is a measured operational benchmark, not a pre-validated production claim.
