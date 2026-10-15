# EA-35 Root-Cause Verification Record

Status: VERIFICATION IN PROGRESS — NOT FINAL LOCKED
Branch: feat/ea35-production-lock-candidate
Prior failing candidate: e860f502f3e1a2d56fd873ad2faab7b1ab630740
Current verified candidate before this record: 6594e816744e8e35eb9d82bda7cce12190eadabb

## Root cause A — core-gates collection failure

The core-gates run for e860f502f3e1a2d56fd873ad2faab7b1ab630740 failed during pytest collection. The log identifies services/gerchain_runtime.py line 275 and reports:
SyntaxError: unexpected character after line continuation character.

The source line contained a literal escaped newline sequence after the fund() signature, causing the function body to be represented as one physical line rather than normal Python source. This created nine collection errors; these were not nine independent behavioral failures.

The source at candidate 6594e816744e8e35eb9d82bda7cce12190eadabb no longer contains that malformed pattern. Exact-SHA core-gates run 38411306665 completed successfully, and its log reports 74 passed plus a second targeted group of 6 passed.

## Root cause B — PostgreSQL migration race

The PostgreSQL Concurrency run for e860f502f3e1a2d56fd873ad2faab7b1ab630740 failed in test_migrations_are_serialized_and_checksum_is_stable. The database log showed duplicate schema_version primary key version=2. The same run reports 5 passed and 1 failed; the NOT_A_STATE check-constraint violation was an expected negative test and was not the suite failure.

The candidate migration runner now:
- acquires a session-level advisory lock for native psycopg before the migration transaction;
- serializes schema-version read/apply/record;
- records versions with ON CONFLICT (version) DO NOTHING and then verifies the recorded checksum;
- retains the SQLAlchemy transaction-scoped migration path;
- fails closed on unresolved migration checksum/schema incompatibilities.

The migration code at candidate 6594e816744e8e35eb9d82bda7cce12190eadabb contains these protections. However, the dedicated PostgreSQL Concurrency workflow must pass on the same candidate SHA before this specific gate can be called verified.

## Exact-SHA evidence at 6594e816744e8e35eb9d82bda7cce12190eadabb

- core-gates run 38411306665: success.
- PostgreSQL Production Runtime run 38411306728: success; log reports 2 passed.
- EA-35 Production PostgreSQL Evidence run 38411306816: success; log reports 18 passed.
- EA-36 Independent PostgreSQL Transaction Graph run 38411307078: success; log reports 1 passed.
- CORE Operating Reconciliation run 38411306291: success.

All above runs report the same head SHA. This is strong technical evidence, but does not itself constitute FINAL LOCK: dedicated PostgreSQL Concurrency on the same SHA, full required-gate inventory, production deployment evidence, and explicit lock approval remain to be reconciled.
