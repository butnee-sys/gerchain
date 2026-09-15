# NEF–G-3–GerChain — ISO/IEC 27001 Gate Closure Matrix

**Status:** Working closure matrix — not certification evidence
**Branch:** `docs/iso27001-alignment`
**Technical CORE baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`

## 1. Closure rule

A gate is **GREEN** only when its defined acceptance criteria are met and objective evidence is traceable. A repository document alone does not prove that an organizational control operates.

## 2. Gate matrix

| Gate | Area | Required closure evidence | Current state | Closure condition |
|---|---|---|---|---|
| G1 | ISMS Scope | approved scope, boundaries, owners, interested parties | OPEN | formal approval |
| G2 | Information Assets | assigned owners, classification, handling rules | PARTIAL | owner/classification completion |
| G3 | Risk | approved risk register, treatment, residual-risk decisions | OPEN | management validation |
| G4 | SoA | approved applicability decisions and rationale | OPEN | formal approval |
| G5 | Controls | implemented controls + operating evidence | PARTIAL | organizational evidence closure |
| G6 | Evidence | complete evidence register and traceability | PARTIAL | evidence-owner validation |
| G7 | Internal Audit | independent audit plan, workpapers, findings, report | NOT STARTED | completed internal audit |
| G8 | Management Review | management inputs, decisions, actions and records | NOT PERFORMED | completed review |
| G9 | Independent Assessment | external/independent assessment and closure of findings | PENDING | assessment completed |

## 3. Priority open evidence

1. Organizational IAM/MFA
2. Privileged-access governance
3. Cryptographic key lifecycle ownership/evidence
4. Backup/restore operational evidence
5. Incident-response records/exercise
6. Supplier register and contractual security requirements
7. Physical-security assessment
8. Legal/regulatory applicability register
9. Personnel-security evidence
10. Independent re-performance

## 4. Technical evidence already available

The matrix recognizes the existing CORE technical evidence, including transaction integrity, PostgreSQL concurrency, release/idempotency, abandoned-processing recovery, reconciliation, cryptographic controls, CI governance, CodeQL and CORE/SHUUD scope separation.

These are supporting technical evidence and do not automatically close organization-level ISMS gates.

## 5. Final lock rule

The NEF–G-3–GerChain ISMS package shall not be described as certified or fully conformant until G1–G9 closure requirements are satisfied by objective evidence and, where applicable, an independent/certification assessment.

## 6. Change control

Changes to the matrix shall be made through the controlled documentation branch and reviewed before inclusion in the final evidence package. CORE production code shall not be changed merely to manufacture ISO documentation evidence.
