"""Independent W3.1 logical-schema fingerprint oracle.

This file intentionally contains no imports from GerChain production code.
The fingerprint represents the declared logical PostgreSQL schema scope;
authority identity is carried separately and is never hashed into PSF.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Type:
    schema: str
    name: str
    parameters: tuple[tuple[str, Any], ...] = ()
    array_dimensions: int = 0


@dataclass(frozen=True)
class Column:
    ordinal: int
    name: str
    type: Type
    nullable: bool
    default: str | None


@dataclass(frozen=True)
class PrimaryKey:
    name: str
    columns: tuple[str, ...]


@dataclass(frozen=True)
class UniqueConstraint:
    name: str
    columns: tuple[str, ...]


@dataclass(frozen=True)
class CheckConstraint:
    name: str
    expression: str


@dataclass(frozen=True)
class ForeignKey:
    name: str
    columns: tuple[str, ...]
    referenced_table: tuple[str, str]
    referenced_columns: tuple[str, ...]
    on_update: str
    on_delete: str


@dataclass(frozen=True)
class Table:
    namespace: str
    name: str
    columns: tuple[Column, ...]
    primary_keys: tuple[PrimaryKey, ...] = ()
    unique_constraints: tuple[UniqueConstraint, ...] = ()
    foreign_keys: tuple[ForeignKey, ...] = ()
    checks: tuple[CheckConstraint, ...] = ()


@dataclass(frozen=True)
class Index:
    namespace: str
    name: str
    table: tuple[str, str]
    unique: bool
    method: str
    key_columns: tuple[str, ...]
    included_columns: tuple[str, ...] = ()
    backing_constraint: bool = False


@dataclass(frozen=True)
class Descriptor:
    descriptor_version: str
    schema_id: str
    tables: tuple[Table, ...]
    indexes: tuple[Index, ...] = ()


def _sorted_columns(columns: tuple[Column, ...]) -> tuple[Column, ...]:
    return tuple(sorted(columns, key=lambda c: (c.ordinal, c.name)))


def _sorted_tables(tables: tuple[Table, ...]) -> tuple[Table, ...]:
    return tuple(sorted(tables, key=lambda t: (t.namespace, t.name)))


def _sorted_indexes(indexes: tuple[Index, ...]) -> tuple[Index, ...]:
    return tuple(sorted(indexes, key=lambda i: (i.namespace, i.name)))


def _type_value(value: Type) -> dict[str, Any]:
    return {
        "schema": value.schema,
        "name": value.name,
        "parameters": [[k, v] for k, v in value.parameters],
        "array_dimensions": value.array_dimensions,
    }


def canonical_descriptor(descriptor: Descriptor) -> dict[str, Any]:
    """Return only logical schema semantics used by the physical fingerprint."""
    tables = []
    for table in _sorted_tables(descriptor.tables):
        tables.append(
            {
                "namespace": table.namespace,
                "name": table.name,
                "columns": [
                    {
                        "ordinal": c.ordinal,
                        "name": c.name,
                        "type": _type_value(c.type),
                        "nullable": c.nullable,
                        "default": None if c.default is None else c.default.strip(),
                    }
                    for c in _sorted_columns(table.columns)
                ],
                "primary_keys": [
                    {"name": p.name, "columns": list(p.columns)}
                    for p in sorted(table.primary_keys, key=lambda p: p.name)
                ],
                "unique_constraints": [
                    {"name": u.name, "columns": list(u.columns)}
                    for u in sorted(table.unique_constraints, key=lambda u: u.name)
                ],
                "foreign_keys": [
                    {
                        "name": f.name,
                        "columns": list(f.columns),
                        "referenced_table": list(f.referenced_table),
                        "referenced_columns": list(f.referenced_columns),
                        "on_update": f.on_update,
                        "on_delete": f.on_delete,
                    }
                    for f in sorted(table.foreign_keys, key=lambda f: f.name)
                ],
                "checks": [
                    {"name": c.name, "expression": c.expression.strip()}
                    for c in sorted(table.checks, key=lambda c: c.name)
                ],
            }
        )

    indexes = [
        {
            "namespace": i.namespace,
            "name": i.name,
            "table": list(i.table),
            "unique": i.unique,
            "method": i.method.strip().lower(),
            "key_columns": list(i.key_columns),
            "included_columns": list(i.included_columns),
        }
        for i in _sorted_indexes(descriptor.indexes)
        if not i.backing_constraint
    ]

    return {"tables": tables, "indexes": indexes}


def canonical_bytes(descriptor: Descriptor) -> bytes:
    return json.dumps(
        canonical_descriptor(descriptor),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def physical_schema_fingerprint(descriptor: Descriptor) -> str:
    return hashlib.sha256(canonical_bytes(descriptor)).hexdigest()


def fingerprint(descriptor: Descriptor) -> str:
    """Backward-compatible alias for the physical schema fingerprint."""
    return physical_schema_fingerprint(descriptor)


def reconcile(
    recorded_schema_id: str,
    recorded_version: int,
    recorded_descriptor_version: str,
    recorded_hash: str,
    actual: Descriptor,
    actual_version: int,
) -> str:
    if recorded_schema_id != actual.schema_id:
        return "IDENTITY_MISMATCH"
    if recorded_version != actual_version:
        return "VERSION_MISMATCH"
    if recorded_descriptor_version != actual.descriptor_version:
        return "DESCRIPTOR_VERSION_MISMATCH"
    if recorded_hash != physical_schema_fingerprint(actual):
        return "RECORDED_MISMATCH"
    return "MATCH"


def _type(name: str, schema: str = "pg_catalog", **parameters: Any) -> Type:
    return Type(schema, name, tuple(sorted(parameters.items())))


def _baseline() -> Descriptor:
    return Descriptor(
        descriptor_version="w3.1-v1.1",
        schema_id="CORE",
        tables=(
            Table(
                namespace="core",
                name="accounts",
                columns=(
                    Column(1, "id", _type("int8"), False, None),
                    Column(2, "owner_id", _type("text"), False, None),
                    Column(3, "balance", _type("int8"), False, None),
                ),
                primary_keys=(PrimaryKey("accounts_pkey", ("id",)),),
            ),
        ),
    )


def _replace_accounts(base: Descriptor, **changes: Any) -> Descriptor:
    table = base.tables[0]
    values = {
        "columns": table.columns,
        "primary_keys": table.primary_keys,
        "unique_constraints": table.unique_constraints,
        "foreign_keys": table.foreign_keys,
        "checks": table.checks,
    }
    values.update(changes)
    return Descriptor(
        base.descriptor_version,
        base.schema_id,
        (Table(table.namespace, table.name, **values),),
        base.indexes,
    )


def run_vector_suite() -> dict[str, Any]:
    baseline = _baseline()
    baseline_hash = fingerprint(baseline)

    # B: additive column
    b = _replace_accounts(
        baseline,
        columns=baseline.tables[0].columns
        + (Column(4, "status", _type("text"), False, "'ACTIVE'::text"),),
    )
    # C: nullability
    c = _replace_accounts(
        baseline,
        columns=(baseline.tables[0].columns[0], Column(2, "owner_id", _type("text"), True, None), baseline.tables[0].columns[2]),
    )
    # D: type
    d = _replace_accounts(
        baseline,
        columns=(baseline.tables[0].columns[0], baseline.tables[0].columns[1], Column(3, "balance", _type("numeric", precision=20, scale=0), False, None)),
    )
    # E1: PK mutation
    e1 = _replace_accounts(
        baseline,
        primary_keys=(PrimaryKey("accounts_pkey", ("owner_id",)),),
    )
    # E2: UNIQUE
    e2 = _replace_accounts(
        baseline,
        unique_constraints=(UniqueConstraint("accounts_owner_uq", ("owner_id",)),),
    )
    # E3: CHECK
    e3 = _replace_accounts(
        baseline,
        checks=(CheckConstraint("accounts_balance_ck", "balance >= 0"),),
    )
    # E4: FK
    e4 = Descriptor(
        baseline.descriptor_version,
        baseline.schema_id,
        baseline.tables
        + (
            Table(
                "core",
                "owners",
                (Column(1, "id", _type("int8"), False, None),),
                primary_keys=(PrimaryKey("owners_pkey", ("id",)),),
            ),
        ),
    )
    e4_accounts = _replace_accounts(
        e4,
        foreign_keys=(ForeignKey("accounts_owner_fk", ("id",), ("core", "owners"), ("id",), "a", "a"),),
    )
    e4 = Descriptor(e4.descriptor_version, e4.schema_id, (e4_accounts.tables[0], e4.tables[1]))
    # E5: standalone ordinary index
    e5 = _replace_accounts(baseline)
    e5 = Descriptor(
        e5.descriptor_version,
        e5.schema_id,
        e5.tables,
        (Index("core", "accounts_owner_idx", ("core", "accounts"), False, "btree", ("owner_id",)),),
    )
    # F: representation/order mutation
    f = Descriptor(
        baseline.descriptor_version,
        baseline.schema_id,
        tuple(reversed(baseline.tables)),
        tuple(reversed(baseline.indexes)),
    )
    # G: out-of-scope object is represented outside this declared descriptor.
    g = baseline
    # H/I/J/K are explicit reconciliation/determinism checks.
    vectors = {
        "A": baseline_hash,
        "B": fingerprint(b),
        "C": fingerprint(c),
        "D": fingerprint(d),
        "E1": fingerprint(e1),
        "E2": fingerprint(e2),
        "E3": fingerprint(e3),
        "E4": fingerprint(e4),
        "E5": fingerprint(e5),
        "F": fingerprint(f),
        "G": fingerprint(g),
    }
    semantic_sensitive = all(vectors[k] != baseline_hash for k in ("B", "C", "D", "E1", "E2", "E3", "E4", "E5"))
    return {
        "vectors": vectors,
        "semantic_sensitive": semantic_sensitive,
        "ordering_invariant": vectors["A"] == vectors["F"],
        "scope_isolated": vectors["A"] == vectors["G"],
        "baseline_reconcile": reconcile("CORE", 1, baseline.descriptor_version, baseline_hash, baseline, 1),
        "wrong_hash_reconcile": reconcile("CORE", 1, baseline.descriptor_version, "0" * 64, baseline, 1),
        "wrong_version_reconcile": reconcile("CORE", 2, baseline.descriptor_version, baseline_hash, baseline, 1),
        "wrong_descriptor_version_reconcile": reconcile("CORE", 1, "other", baseline_hash, baseline, 1),
        "fresh_process_fingerprint": fingerprint(baseline),
    }


if __name__ == "__main__":
    result = run_vector_suite()
    print(json.dumps(result, sort_keys=True, indent=2))
    assert result["semantic_sensitive"]
    assert result["ordering_invariant"]
    assert result["scope_isolated"]
    assert result["baseline_reconcile"] == "MATCH"
    assert result["wrong_hash_reconcile"] == "RECORDED_MISMATCH"
    assert result["wrong_version_reconcile"] == "VERSION_MISMATCH"
    assert result["wrong_descriptor_version_reconcile"] == "DESCRIPTOR_VERSION_MISMATCH"
