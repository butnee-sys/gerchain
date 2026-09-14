# CORE / SHUUD Scope Boundary

SHUUD application validation is separate from GerChain CORE assurance.

CORE PostgreSQL gates cover GerChain infrastructure controls. SHUUD PostgreSQL persistence, API, sandbox, restart-recovery and application end-to-end tests remain in SHUUD-specific workflows.

A SHUUD application test failure must not make a CORE infrastructure control appear failed.

PwC-style CORE evidence explicitly excludes SHUUD unless the audit scope is formally expanded.

Frozen CORE audit baseline: `274f45c83ce088e2229a2628e3a80403a68503df`
