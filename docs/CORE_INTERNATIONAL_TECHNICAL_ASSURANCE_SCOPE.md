# GerChain CORE — International Technical Assurance Scope

## Scope

This assurance package covers **GerChain CORE only**:

- Money Ledger / Engine
- Escrow Engine
- Witness Chain
- Idempotency
- Outbox / Recovery
- PostgreSQL transaction integrity and concurrency
- Reconciliation
- Cryptographic / decision controls
- CI/CD and repository governance
- Audit evidence and security documentation

## Explicit exclusions

The following are **outside this assurance scope** and must not be treated as CORE assurance failures or evidence:

- SHUUD application and sandbox
- SHUUD command layer
- SHUUD API / E2E flows
- SHUUD-specific business logic
- SHUUD-specific workflow failures
- SHUUD-specific PostgreSQL or application tests

## Assurance layers

1. CORE technical controls and test evidence
2. OpenSSF Scorecard / OSPS evidence where applicable
3. CodeQL security analysis
4. Dependency and SBOM evidence
5. Secret/repository hygiene evidence
6. MNS ISO/IEC 27001:2023 evidence mapping
7. Independent assurance — not claimed until independently performed

## Claims policy

Passing automated checks is technical evidence only. It is not an ISO/IEC 27001 certification, independent audit opinion, or organizational attestation.

GerChain CORE remains proprietary. No open-source license is added merely to obtain an OpenSSF badge.
