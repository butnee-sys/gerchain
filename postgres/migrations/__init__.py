from __future__ import annotations

from pathlib import Path
import hashlib
import re

from sqlalchemy import text

_VERSION_RE = re.compile(r"^(\d+)_.*\.sql$")
_LOCK_KEY = 8342719

# One authoritative migration file per schema version. Other files sharing the
# same numeric prefix are retained as historical evidence and are never applied
# on a fresh database. Their checksums remain accepted for already-published
# schema history so legacy databases can be re-entered safely.
_PREFERRED_MIGRATIONS = {
    1: "001_canonical_production.sql",
    2: "002_canonical_production.sql",
    3: "003_canonical_compatibility.sql",
    4: "004_canonical_value_truth.sql",
    5: "005_canonical_production.sql",
    6: "006_canonical_movement_integrity.sql",
    7: "007_canonical_production_reconciliation.sql",
    8: "008_ea35_idempotency_compat.sql",
    9: "009_canonical_movement_integrity_hardening.sql",
    10: "010_canonical_evidence_constraints.sql",
    11: "011_ea35_canonical_schema_finalization.sql",
    12: "012_canonical_production.sql",
}


def _execute(connection, sql: str, params: dict | None = None):
    """Execute against either SQLAlchemy Connection or psycopg Connection."""
    if hasattr(connection, "exec_driver_sql"):
        return connection.exec_driver_sql(
            sql,
            params,
            execution_options={"no_parameters": True} if params is None else {},
        )
    if params:
        # Migration parameters are restricted to integer version and SHA-256 hex.
        sql = sql.replace(":version", "%s").replace(":checksum", "%s")
        ordered = [params["version"], params["checksum"]]
        return connection.execute(sql, ordered)
    return connection.execute(sql)



def apply_migrations(connection, migration_dir: Path) -> None:
    """Apply ordered PostgreSQL migrations exactly once with checksum locking."""
    # Session-level advisory lock makes concurrent first boots mutually exclusive.
    # This is deliberately explicit: migration runners may be invoked through
    # different PostgreSQL/psycopg transaction wrappers, so the lock lifetime
    # must not depend on implicit transaction semantics.
    _execute(connection, "SELECT pg_advisory_lock(8342719)")
    try:
        _execute(
            connection,
            "CREATE TABLE IF NOT EXISTS schema_version ("
            "version BIGINT PRIMARY KEY, "
            "checksum TEXT NOT NULL, "
            "applied_at TIMESTAMPTZ NOT NULL DEFAULT now()"
            ")",
        )

        files = sorted(
            p for p in migration_dir.glob("*.sql")
            if _VERSION_RE.match(p.name)
        )
        by_version: dict[int, list[Path]] = {}
        for path in files:
            version = int(_VERSION_RE.match(path.name).group(1))
            by_version.setdefault(version, []).append(path)

        selected: list[tuple[int, Path, set[str]]] = []
        for version in sorted(by_version):
            candidates = by_version[version]
            preferred_name = _PREFERRED_MIGRATIONS.get(version)
            preferred = next((p for p in candidates if p.name == preferred_name), None)
            if preferred is None:
                if len(candidates) != 1:
                    raise RuntimeError(
                        f"migration version {version} has no unique authoritative file: "
                        + ", ".join(p.name for p in candidates)
                    )
                preferred = candidates[0]
            historical_checksums = {
                hashlib.sha256(p.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
                for p in candidates
            }
            selected.append((version, preferred, historical_checksums))

        for version, path, historical_checksums in selected:
            sql = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()

            if hasattr(connection, "exec_driver_sql"):
                row = connection.execute(
                    text("SELECT checksum FROM schema_version WHERE version = :version"),
                    {"version": version},
                ).scalar_one_or_none()
            else:
                row = connection.execute(
                    "SELECT checksum FROM schema_version WHERE version = %s",
                    (version,),
                ).fetchone()
                row = row[0] if row else None

            if row is not None:
                if row != checksum and row not in historical_checksums:
                    raise RuntimeError(
                        f"migration checksum mismatch for version {version}: "
                        f"database={row} file={checksum}"
                    )
                continue

            if hasattr(connection, "exec_driver_sql"):
                connection.exec_driver_sql(
                    sql,
                    execution_options={"no_parameters": True},
                )
                connection.execute(
                    text(
                        "INSERT INTO schema_version(version, checksum) "
                        "VALUES (:version, :checksum) "
                        "ON CONFLICT (version) DO NOTHING"
                    ),
                    {"version": version, "checksum": checksum},
                )
                recorded = connection.execute(
                    text("SELECT checksum FROM schema_version WHERE version = :version"),
                    {"version": version},
                ).scalar_one()
                if recorded != checksum and recorded not in historical_checksums:
                    raise RuntimeError(
                        f"migration checksum mismatch for version {version}: "
                        f"database={recorded} file={checksum}"
                    )
            else:
                connection.execute(sql)
                connection.execute(
                    "INSERT INTO schema_version(version, checksum) VALUES (%s, %s)",
                    (version, checksum),
                )

        connection.commit()
    finally:
        try:
            _execute(connection, "SELECT pg_advisory_unlock(8342719)")
        finally:
            if hasattr(connection, "rollback"):
                connection.rollback()
