# SHUUD Sandbox Case Intake

Day-0 sandbox registration now has a concrete case-intake boundary.

## Flow

1. A canonical SHUUD incident is created through the existing incident API.
2. The incident is bound to an active sandbox with:
   `POST /api/v1/shuud/sandbox/config/{sandbox_id}/cases/{incident_id}`
3. The binding is persisted inside the existing canonical incident snapshot.
4. Evidence, SHIID, clearance, escrow, release, and economic measurement continue through the existing SHUUD lifecycle.
5. KPI and command layers continue to read persisted evidence; intake does not calculate or invent economic values.

## Authority boundary

Case intake is an association, not a second lifecycle. It does not create a new WitnessChain, EscrowEngine, or case state machine.
