# GerChain CORE — Snyk Container Remediation

Scope: GerChain CORE container/base-image security only. SHUUD is frozen and out of scope.

Baseline: `python:3.9-slim`; 4 Critical, 14 High, 4 Medium, 130 Low; 152 total; 92 fixable; 60 no supported fix; 0 known exploit.

First remediation candidate: stable Python 3.13 slim, subject to full CORE regression and fresh Snyk retest. Python 3.15 release candidates and Alpine are not the first remediation baseline.

Acceptance gates:
1. Docker build succeeds.
2. CORE runtime starts.
3. CORE tests remain green.
4. PostgreSQL Concurrency remains green.
5. CORE Operating Reconciliation remains green.
6. CodeQL remains green.
7. Snyk retest completed.
8. Critical findings = 0.
9. Remaining findings remediated or documented with residual-risk/mitigation evidence.
10. SHUUD remains out of scope.

Final evidence to populate after remediation: commit, retest date, C/H/M/L counts, unsupported findings, CI evidence, final gate status.
