# ISO/IEC 27001:2023 — WP1/WP3 IAM, MFA and Privileged Access Execution Checklist

**Status:** Controlled execution checklist  
**Branch:** `docs/iso27001-alignment`  
**CORE baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`

## Objective

Close the highest-risk identity controls first without modifying the frozen GerChain CORE merely for documentation.

## Control scope

- A.5.2 — Information security roles and responsibilities
- A.5.3 — Segregation of duties
- A.5.4 — Management responsibilities
- A.5.15 — Access control
- A.5.16 — Identity management
- A.5.17 — Authentication information
- A.5.18 — Access rights
- A.8.2 — Privileged access rights
- A.8.3 — Information access restriction
- A.8.5 — Secure authentication

## Evidence required

### E1 — Identity register

Record every in-scope human/service identity, owner, role, environment, privilege level, authentication method, status, creation date and termination/review date.

### E2 — MFA evidence

Retain objective evidence that MFA is enforced for privileged and security-sensitive access, including approved exceptions and their expiry dates.

### E3 — Privileged access register

Identify privileged accounts, privilege rationale, approving authority, allowed actions, review frequency and emergency-access treatment.

### E4 — Access review

Perform a dated access review and record additions, removals, downgrades, exceptions and reviewer decision.

### E5 — Segregation of duties

Define incompatible roles and verify that no single person can unilaterally perform conflicting critical actions where separation is required.

### E6 — Offboarding/change

Demonstrate that role changes and termination trigger timely access modification or revocation.

### E7 — Repository governance

Use GitHub branch protection, required review and status checks as supporting evidence only. Repository governance does not by itself prove organization-wide IAM/MFA.

## Acceptance test

A control may move from GAP/PARTIAL toward GREEN only after:

`Evidence source → owner → date/version → reviewer → decision → retained record`

is complete.

## Security restriction

Never place passwords, API tokens, private keys, recovery codes, production credentials or other secrets in this repository.

## Current state

**NOT CLOSED.** The repository contains the control requirements and technical supporting evidence, but actual organizational identity/MFA/privileged-access records must be supplied and reviewed before these controls can be marked GREEN.
