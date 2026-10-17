"""Read-only PostgreSQL logical-schema observation for CORE W3.1-B.

This module observes the declared W3.1 v1.1 schema scope only. It never
creates, alters, drops, repairs, or records schema state.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection


DESCRIPTOR_VERSION = "w3.1-v1.1"


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
    tables: tuple[Table, ...] = ()
    indexes: tuple[Index, ...] = ()


_SCOPE_RELKINDS = {"r"}


def _type_from_row(row: Any) -> Type:
    parameters: tuple[tuple[str, Any], ...] = ()
    if row.typmod is not None and row.typmod >= 0:
        parameters = (("typmod", int(row.typmod)),)
    return Type(row.type_schema, row.type_name, parameters, int(row.array_dimensions or 0))


def _action(code: str) -> str:
    return {
        "a": "NO ACTION",
        "r": "RESTRICT",
        "c": "CASCADE",
        "n": "SET NULL",
        "d": "SET DEFAULT",
    }.get(code, code)


def observe(conn: Connection, schema_id: str, namespaces: tuple[str, ...] = ("core",)) -> Descriptor:
    """Observe PostgreSQL catalog state without mutating it."""
    if not namespaces:
        raise ValueError("at least one declared namespace is required")
    bind = {f"n{i}": value for i, value in enumerate(namespaces)}
    namespace_sql = ", ".join(f":n{i}" for i in range(len(namespaces)))

    tables = conn.execute(
        text(
            f"""SELECT n.nspname AS namespace, c.relname AS name
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname IN ({namespace_sql}) AND c.relkind IN ('r')
                ORDER BY n.nspname, c.relname"""
        ),
        bind,
    ).mappings().all()

    descriptors: list[Table] = []
    for table_row in tables:
        namespace = table_row["namespace"]
        table_name = table_row["name"]
        columns = conn.execute(
            text(
                """SELECT a.attnum AS ordinal, a.attname AS name,
                          a.attnotnull AS nullable_not, a.atttypmod AS typmod,
                          a.attndims AS array_dimensions,
                          t.typname AS type_name,
                          tn.nspname AS type_schema,
                          pg_get_expr(ad.adbin, ad.adrelid) AS default_expression
                   FROM pg_catalog.pg_attribute a
                   JOIN pg_catalog.pg_type t ON t.oid = a.atttypid
                   JOIN pg_catalog.pg_namespace tn ON tn.oid = t.typnamespace
                   LEFT JOIN pg_catalog.pg_attrdef ad
                     ON ad.adrelid = a.attrelid AND ad.adnum = a.attnum
                   WHERE a.attrelid = to_regclass(:qualified_table)::oid
                     AND a.attnum > 0 AND NOT a.attisdropped
                   ORDER BY a.attnum"""
            ),
            {"qualified_table": f'"{namespace}"."{table_name}"'},
        ).mappings().all()

        column_values = tuple(
            Column(
                int(row["ordinal"]),
                row["name"],
                _type_from_row(row),
                not bool(row["nullable_not"]),
                row["default_expression"].strip() if row["default_expression"] else None,
            )
            for row in columns
        )

        constraints = conn.execute(
            text(
                """SELECT con.conname, con.contype,
                          con.conkey::int[] AS local_keys,
                          con.confkey::int[] AS foreign_keys,
                          fn.nspname AS foreign_schema,
                          fc.relname AS foreign_table,
                          con.confupdtype, con.confdeltype,
                          pg_get_constraintdef(con.oid, true) AS definition
                   FROM pg_catalog.pg_constraint con
                   JOIN pg_catalog.pg_class c ON c.oid = con.conrelid
                   JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                   LEFT JOIN pg_catalog.pg_class fc ON fc.oid = con.confrelid
                   LEFT JOIN pg_catalog.pg_namespace fn ON fn.oid = fc.relnamespace
                   WHERE n.nspname = :namespace AND c.relname = :table_name
                     AND con.contype IN ('p','u','c','f')
                   ORDER BY con.conname"""
            ),
            {"namespace": namespace, "table_name": table_name},
        ).mappings().all()
        by_attnum = {int(row["ordinal"]): row["name"] for row in columns}
        primary: list[PrimaryKey] = []
        uniques: list[UniqueConstraint] = []
        checks: list[CheckConstraint] = []
        foreign: list[ForeignKey] = []
        for row in constraints:
            local = tuple(by_attnum[int(v)] for v in (row["local_keys"] or []))
            if row["contype"] == "p":
                primary.append(PrimaryKey(row["conname"], local))
            elif row["contype"] == "u":
                uniques.append(UniqueConstraint(row["conname"], local))
            elif row["contype"] == "c":
                checks.append(CheckConstraint(row["conname"], row["definition"]))
            elif row["contype"] == "f":
                ref_rows = conn.execute(
                    text(
                        """SELECT a.attname
                           FROM pg_catalog.pg_attribute a
                           WHERE a.attrelid = to_regclass(:qualified_ref)::oid
                             AND a.attnum = ANY(:keys)
                           ORDER BY array_position(:keys, a.attnum)"""
                    ),
                    {
                        "qualified_ref": f'"{row["foreign_schema"]}"."{row["foreign_table"]}"',
                        "keys": list(row["foreign_keys"] or []),
                    },
                ).mappings().all()
                foreign.append(
                    ForeignKey(
                        row["conname"],
                        local,
                        (row["foreign_schema"], row["foreign_table"]),
                        tuple(v["attname"] for v in ref_rows),
                        _action(row["confupdtype"]),
                        _action(row["confdeltype"]),
                    )
                )

        descriptors.append(
            Table(
                namespace,
                table_name,
                column_values,
                tuple(primary),
                tuple(uniques),
                tuple(foreign),
                tuple(checks),
            )
        )

    indexes: list[Index] = []
    for row in conn.execute(
        text(
            f"""SELECT n.nspname AS namespace, i.relname AS index_name,
                      tn.nspname AS table_namespace, t.relname AS table_name,
                      ix.indisunique AS unique_index, am.amname AS method,
                      ix.indkey::int[] AS key_attnums,
                      ix.indnkeyatts, ix.indnatts,
                      ix.indpred IS NOT NULL AS partial,
                      ix.indexprs IS NOT NULL AS expression,
                      EXISTS (
                        SELECT 1 FROM pg_catalog.pg_constraint c
                        WHERE c.conindid = ix.indexrelid AND c.contype IN ('p','u')
                      ) AS backing_constraint
               FROM pg_catalog.pg_index ix
               JOIN pg_catalog.pg_class i ON i.oid = ix.indexrelid
               JOIN pg_catalog.pg_class t ON t.oid = ix.indrelid
               JOIN pg_catalog.pg_namespace n ON n.oid = i.relnamespace
               JOIN pg_catalog.pg_namespace tn ON tn.oid = t.relnamespace
               JOIN pg_catalog.pg_am am ON am.oid = i.relam
               WHERE tn.nspname IN ({namespace_sql})
               ORDER BY n.nspname, i.relname"""
        ),
        bind,
    ).mappings().all():
        if row["partial"] or row["expression"] or row["backing_constraint"]:
            continue
        column_rows = conn.execute(
            text(
                """SELECT a.attname, s.position
                   FROM unnest(:keys) WITH ORDINALITY AS s(attnum, position)
                   JOIN pg_catalog.pg_attribute a
                     ON a.attrelid = to_regclass(:qualified_table)::oid AND a.attnum = s.attnum
                   WHERE s.position <= :total_count
                   ORDER BY s.position"""
            ),
            {
                "keys": list(row["key_attnums"] or []),
                "qualified_table": f'"{row["table_namespace"]}"."{row["table_name"]}"',
                "total_count": int(row["indnatts"]),
            },
        ).mappings().all()
        key_count = int(row["indnkeyatts"])
        key_columns = tuple(v["attname"] for v in column_rows[:key_count])
        included_columns = tuple(v["attname"] for v in column_rows[key_count:])
        indexes.append(
            Index(
                row["namespace"],
                row["index_name"],
                (row["table_namespace"], row["table_name"]),
                bool(row["unique_index"]),
                row["method"],
                key_columns,
                included_columns,
            )
        )

    return Descriptor(DESCRIPTOR_VERSION, schema_id, tuple(descriptors), tuple(indexes))


def canonical_descriptor(descriptor: Descriptor) -> dict[str, Any]:
    def typ(v: Type) -> dict[str, Any]:
        return {"schema": v.schema, "name": v.name, "parameters": [[k, x] for k, x in v.parameters], "array_dimensions": v.array_dimensions}
    return {
        "tables": [
            {
                "namespace": t.namespace,
                "name": t.name,
                "columns": [{"ordinal": c.ordinal, "name": c.name, "type": typ(c.type), "nullable": c.nullable, "default": c.default} for c in sorted(t.columns, key=lambda c: (c.ordinal, c.name))],
                "primary_keys": [{"name": x.name, "columns": list(x.columns)} for x in sorted(t.primary_keys, key=lambda x: x.name)],
                "unique_constraints": [{"name": x.name, "columns": list(x.columns)} for x in sorted(t.unique_constraints, key=lambda x: x.name)],
                "foreign_keys": [{"name": x.name, "columns": list(x.columns), "referenced_table": list(x.referenced_table), "referenced_columns": list(x.referenced_columns), "on_update": x.on_update, "on_delete": x.on_delete} for x in sorted(t.foreign_keys, key=lambda x: x.name)],
                "checks": [{"name": x.name, "expression": x.expression.strip()} for x in sorted(t.checks, key=lambda x: x.name)],
            }
            for t in sorted(descriptor.tables, key=lambda t: (t.namespace, t.name))
        ],
        "indexes": [
            {"namespace": x.namespace, "name": x.name, "table": list(x.table), "unique": x.unique, "method": x.method.strip().lower(), "key_columns": list(x.key_columns), "included_columns": list(x.included_columns)}
            for x in sorted(descriptor.indexes, key=lambda x: (x.namespace, x.name)) if not x.backing_constraint
        ],
    }


def physical_schema_fingerprint(descriptor: Descriptor) -> str:
    payload = json.dumps(canonical_descriptor(descriptor), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def reconcile(conn: Connection, schema_id: str, expected_hash: str, namespaces: tuple[str, ...] = ("core",)) -> tuple[Descriptor, str]:
    descriptor = observe(conn, schema_id, namespaces)
    return descriptor, physical_schema_fingerprint(descriptor)
