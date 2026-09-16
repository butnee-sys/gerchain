"""Independent W3.1 schema fingerprint oracle.

This file intentionally contains no imports from GerChain production code.
It defines a small deterministic canonicalization model that can be fed
PostgreSQL catalog observations by an external runner.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Column:
    ordinal: int
    name: str
    data_type: str
    nullable: bool
    default: str | None


@dataclass(frozen=True)
class Table:
    namespace: str
    name: str
    columns: tuple[Column, ...]
    primary_key: tuple[str, ...]
    unique_constraints: tuple[tuple[str, ...], ...]
    foreign_keys: tuple[tuple[str, tuple[str, ...], str, tuple[str, ...], str, str], ...]
    checks: tuple[str, ...]


@dataclass(frozen=True)
class Index:
    namespace: str
    name: str
    table: str
    unique: bool
    method: str
    definition: str


@dataclass(frozen=True)
class Descriptor:
    descriptor_version: str
    schema_id: str
    tables: tuple[Table, ...]
    indexes: tuple[Index, ...]


def _sorted_columns(columns: tuple[Column, ...]) -> tuple[Column, ...]:
    return tuple(sorted(columns, key=lambda c: (c.ordinal, c.name)))


def _sorted_tables(tables: tuple[Table, ...]) -> tuple[Table, ...]:
    return tuple(
        sorted(
            tables,
            key=lambda t: (t.namespace, t.name),
        )
    )


def _sorted_indexes(indexes: tuple[Index, ...]) -> tuple[Index, ...]:
    return tuple(sorted(indexes, key=lambda i: (i.namespace, i.name)))


def canonical_descriptor(descriptor: Descriptor) -> dict[str, Any]:
    """Return a deterministic, JSON-compatible representation."""
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
                        "data_type": c.data_type.strip(),
                        "nullable": c.nullable,
                        "default": None if c.default is None else c.default.strip(),
                    }
                    for c in _sorted_columns(table.columns)
                ],
                "primary_key": list(table.primary_key),
                "unique_constraints": [
                    list(v) for v in sorted(table.unique_constraints)
                ],
                "foreign_keys": [
                    [
                        name,
                        list(columns),
                        referenced_table,
                        list(referenced_columns),
                        on_update,
                        on_delete,
                    ]
                    for name, columns, referenced_table, referenced_columns, on_update, on_delete
                    in sorted(table.foreign_keys)
                ],
                "checks": sorted(table.checks),
            }
        )

    indexes = [
        {
            "namespace": i.namespace,
            "name": i.name,
            "table": i.table,
            "unique": i.unique,
            "method": i.method.strip().lower(),
            "definition": i.definition.strip(),
        }
        for i in _sorted_indexes(descriptor.indexes)
    ]

    return {
        "descriptor_version": descriptor.descriptor_version,
        "schema_id": descriptor.schema_id,
        "tables": tables,
        "indexes": indexes,
    }


def canonical_bytes(descriptor: Descriptor) -> bytes:
    return json.dumps(
        canonical_descriptor(descriptor),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def fingerprint(descriptor: Descriptor) -> str:
    return hashlib.sha256(canonical_bytes(descriptor)).hexdigest()


def reconcile(recorded_schema_id: str, recorded_hash: str, actual: Descriptor) -> str:
    if recorded_schema_id != actual.schema_id:
        return "IDENTITY_MISMATCH"
    if recorded_hash != fingerprint(actual):
        return "RECORDED_MISMATCH"
    return "MATCH"


def _baseline() -> Descriptor:
    return Descriptor(
        descriptor_version="w3.1-v1",
        schema_id="CORE",
        tables=(
            Table(
                namespace="core",
                name="accounts",
                columns=(
                    Column(1, "id", "bigint", False, None),
                    Column(2, "owner_id", "text", False, None),
                    Column(3, "balance", "bigint", False, None),
                ),
                primary_key=("id",),
                unique_constraints=(),
                foreign_keys=(),
                checks=(),
            ),
        ),
        indexes=(),
    )


def run_vector_suite() -> dict[str, Any]:
    baseline = _baseline()
    baseline_hash = fingerprint(baseline)

    reordered = Descriptor(
        descriptor_version=baseline.descriptor_version,
        schema_id=baseline.schema_id,
        tables=tuple(reversed(baseline.tables)),
        indexes=tuple(reversed(baseline.indexes)),
    )

    changed = Descriptor(
        descriptor_version=baseline.descriptor_version,
        schema_id=baseline.schema_id,
        tables=(
            Table(
                namespace="core",
                name="accounts",
                columns=baseline.tables[0].columns
                + (Column(4, "status", "text", False, "'ACTIVE'"),),
                primary_key=("id",),
                unique_constraints=(),
                foreign_keys=(),
                checks=(),
            ),
        ),
        indexes=(),
    )

    return {
        "baseline_fingerprint": baseline_hash,
        "ordering_invariant": baseline_hash == fingerprint(reordered),
        "semantic_mutation_detected": baseline_hash != fingerprint(changed),
        "baseline_reconcile": reconcile("CORE", baseline_hash, baseline),
        "mutation_reconcile": reconcile("CORE", baseline_hash, changed),
        "wrong_identity_reconcile": reconcile("OTHER", baseline_hash, baseline),
    }


if __name__ == "__main__":
    result = run_vector_suite()
    print(json.dumps(result, sort_keys=True, indent=2))
    assert result["ordering_invariant"]
    assert result["semantic_mutation_detected"]
    assert result["baseline_reconcile"] == "MATCH"
    assert result["mutation_reconcile"] == "RECORDED_MISMATCH"
    assert result["wrong_identity_reconcile"] == "IDENTITY_MISMATCH"
