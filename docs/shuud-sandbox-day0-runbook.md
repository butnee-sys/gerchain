# SHUUD Sandbox Day-0 Runbook

## 0. Rule

Day-0 proves that the sandbox environment is operational. It is not the start of unrestricted live processing.

## 1. Deploy

1. Checkout the current `main` baseline.
2. Provision an isolated PostgreSQL 16 database.
3. Configure `SHUUD_PERSISTENCE_URL` for the sandbox database.
4. Start the GerChain/SHUUD runtime.
5. Verify API health and measurement endpoints.

## 2. Verify state authority

Confirm:

- one WitnessChain authority;
- one EscrowEngine authority;
- SHUUD persistence used only for durable recovery;
- MNT amount/currency semantics are preserved;
- NEF remains the settlement provider/infrastructure.

## 3. Execute smoke cases

Run S1–S10 from the scenario matrix. At minimum, complete S1, S3, S4, S5 and S6 before admitting participant test traffic.

## 4. Record

For every case record:

- incident ID;
- timestamps;
- evidence result;
- verification result;
- SHIID decision;
- clearance result;
- escrow result;
- settlement result;
- measurement summary;
- exception/escalation reason, if any.

## 5. Day-0 go/no-go

### GO
All required technical smoke cases pass, measurement records are queryable, audit records are complete, and manual fallback is available.

### NO-GO
Any state-authority conflict, data-loss issue, unsafe release behavior, unrecoverable restart state, or un-auditable decision occurs.

A NO-GO result creates a corrective-action item; it does not become a negative operational KPI.
