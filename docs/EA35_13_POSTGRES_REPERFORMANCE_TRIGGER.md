# EA-35.13 PostgreSQL re-performance trigger

This marker intentionally contains no runtime or architecture change.

Purpose:
- trigger the branch-scoped PostgreSQL production proof workflows;
- capture fresh evidence against the current branch tip;
- do not treat prior workflow failures as current GREEN evidence.

Gate remains NOT LOCKED until the fresh PostgreSQL runs complete successfully.
