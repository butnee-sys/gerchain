# Trivy CORE Security Scan

## Scope

This scan covers **GerChain CORE only**. SHUUD is frozen and explicitly out of scope.

## Purpose

Trivy provides an additional independent automated technical signal alongside the locked Snyk container baseline. It scans the built CORE Docker image and the repository filesystem for vulnerabilities, secrets, and misconfiguration.

## Locked Snyk baseline

- Critical: 4
- High: 14
- Medium: 4
- Low: 130
- Total: 152

The Snyk baseline remains immutable evidence. Trivy results are separate evidence and do not replace Snyk.

## Candidate result

Candidate: `7f051b4dc742553198173f551196ca9d43e757fd`

Trivy CORE image report:

- Critical: **0**
- High: **0**
- Medium: **0**

The Trivy workflow completed successfully. The candidate uses a clean Alpine 3.22 multi-stage runtime and excludes `sandbox/` from the CORE filesystem scan because SHUUD is frozen and out of scope.

## Gate status

**Automated Trivy gate: GREEN.**

This does not by itself constitute certification or final security approval. Candidate-specific external verification and independent technical re-performance remain required before merge.
