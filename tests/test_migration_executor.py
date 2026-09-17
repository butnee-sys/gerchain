from core.migration_identity import MigrationIdentity
from persistence.migration_executor import MigrationBypassError, MigrationDefinition, migration_hash


def _definition(statements):
    identity = MigrationIdentity(
        migration_id="m-1",
        schema_id="CORE",
        from_version=1,
        to_version=2,
        migration_hash=migration_hash(tuple(statements)),
    )
    return MigrationDefinition(identity, tuple(statements), expected_schema_hash="a" * 64)


def test_migration_hash_is_stable_under_whitespace():
    a = ("CREATE TABLE core.example (id bigint PRIMARY KEY)",)
    b = ("  CREATE   TABLE core.example (id bigint PRIMARY KEY); ",)
    assert migration_hash(a) == migration_hash(b)


def test_definition_rejects_hash_tampering():
    definition = _definition(("CREATE TABLE core.example (id bigint PRIMARY KEY)",))
    tampered = MigrationDefinition(
        MigrationIdentity("m-1", "CORE", 1, 2, "b" * 64),
        definition.statements,
        definition.expected_schema_hash,
    )
    try:
        tampered.validate()
    except Exception as exc:
        assert "migration_hash" in str(exc)
    else:
        raise AssertionError("tampered migration hash was accepted")


def test_definition_rejects_transaction_control():
    definition = _definition(("CREATE TABLE core.example (id bigint PRIMARY KEY); COMMIT",))
    try:
        definition.validate()
    except MigrationBypassError:
        pass
    else:
        raise AssertionError("transaction control was accepted")


def test_definition_rejects_unsupported_ddl():
    definition = _definition(("DROP TABLE core.example",))
    try:
        definition.validate()
    except MigrationBypassError:
        pass
    else:
        raise AssertionError("unsupported DDL was accepted")
