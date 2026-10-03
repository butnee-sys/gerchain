from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy import text


def apply_migrations(connection, migration_dir: Path) -> None:
    migration_dir = Path(migration_dir)
    migration_files = sorted(
        migration_dir.glob("*.sql"),
        key=lambda path: int(path.name.split("_", 1)[0]),
    )

    # Migrations own their transaction boundary. This is required for the
    # advisory lock to serialize both DDL and schema_version commits; releasing
    # the lock before commit allows a second migrator to observe stale history.
    is_sqlalchemy = hasattr(connection, "exec_driver_sql")

    if is_sqlalchemy:
        from sqlalchemy import text

    def execute(sql: str, params=None, *, static_sql: bool = False):
        if is_sqlalchemy:
            if static_sql:
                # Static migration SQL may contain literal percent signs (e.g. LIKE
                # patterns). Execute through the DBAPI boundary with %% escaping;
                # control statements continue to use SQLAlchemy bind parameters.
                return connection.exec_driver_sql(
                    sql.replace("%", "%%"),
                    {},
                )
            return connection.execute(text(sql), params or {})
        if static_sql:
            sql = sql.replace("%", "%%")
        return connection.execute(sql, params or ())

    lock_key = "gerchain:migrations"
    if is_sqlalchemy:
        execute(
            "SELECT pg_advisory_lock(hashtext(:lock_key))",
            {"lock_key": lock_key},
        )
    else:
        execute(
            "SELECT pg_advisory_lock(hashtext(%s))",
            (lock_key,),
        )

    try:
        execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version BIGINT PRIMARY KEY,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )

        applied_rows = execute("SELECT version, checksum FROM schema_version")
        applied = {int(row[0]): row[1] for row in applied_rows}

        for path in migration_files:
            version = int(path.name.split("_", 1)[0])
            sql = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()

            if version in applied:
                if applied[version] != checksum:
                    raise RuntimeError(
                        f"migration checksum mismatch for version {version}: {path.name}"
                    )
                continue

            execute(sql, static_sql=True)

            if is_sqlalchemy:
                recorded = execute(
                    "INSERT INTO schema_version(version, checksum) "
                    "VALUES (:version, :checksum) "
                    "ON CONFLICT (version) DO NOTHING "
                    "RETURNING checksum",
                    {"version": version, "checksum": checksum},
                ).scalar_one_or_none()
                if recorded is None:
                    recorded = execute(
                        "SELECT checksum FROM schema_version WHERE version = :version",
                        {"version": version},
                    ).scalar_one()
            else:
                recorded_cursor = execute(
                    "INSERT INTO schema_version(version, checksum) "
                    "VALUES (%s, %s) "
                    "ON CONFLICT (version) DO NOTHING "
                    "RETURNING checksum",
                    (version, checksum),
                )
                recorded_row = recorded_cursor.fetchone()
                if recorded_row is None:
                    recorded_row = execute(
                        "SELECT checksum FROM schema_version WHERE version = %s",
                        (version,),
                    ).fetchone()
                recorded = recorded_row[0]

            if recorded != checksum:
                raise RuntimeError(
                    f"migration checksum mismatch for version {version}: {path.name}"
                )

        # Commit BEFORE releasing the session-level advisory lock. Otherwise
        # another migrator can acquire the lock and race against an uncommitted
        # schema_version row.
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        if is_sqlalchemy:
            execute("SELECT pg_advisory_unlock(hashtext(:lock_key))", {"lock_key": lock_key})
        else:
            execute("SELECT pg_advisory_unlock(hashtext(%s))", (lock_key,))
