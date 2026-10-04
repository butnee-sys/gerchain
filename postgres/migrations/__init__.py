from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy import text


def _split_sql_statements(sql: str) -> list[str]:
    """Split PostgreSQL SQL on top-level semicolons, preserving dollar blocks."""
    statements: list[str] = []
    start = 0
    i = 0
    n = len(sql)
    quote: str | None = None
    dollar_tag: str | None = None
    line_comment = False
    block_comment = False

    while i < n:
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""
        if line_comment:
            if ch == "\n": line_comment = False
            i += 1; continue
        if block_comment:
            if ch == "*" and nxt == "/": block_comment = False; i += 2; continue
            i += 1; continue
        if dollar_tag is not None:
            if sql.startswith(dollar_tag, i):
                tag_length = len(dollar_tag)
                dollar_tag = None
                i += tag_length
                continue
            i += 1; continue
        if quote is not None:
            if ch == quote:
                if i + 1 < n and sql[i + 1] == quote: i += 2; continue
                quote = None
            i += 1; continue
        if ch == "-" and nxt == "-": line_comment = True; i += 2; continue
        if ch == "/" and nxt == "*": block_comment = True; i += 2; continue
        if ch in ("'", '"'): quote = ch; i += 1; continue
        if ch == "$":
            end = sql.find("$", i + 1)
            if end != -1:
                candidate = sql[i:end + 1]
                tag = candidate[1:-1]
                if candidate == "$$" or (tag and all(c.isalnum() or c == "_" for c in tag)):
                    dollar_tag = candidate; i = end + 1; continue
        if ch == ";":
            statement = sql[start:i].strip()
            if statement: statements.append(statement)
            start = i + 1
        i += 1
    tail = sql[start:].strip()
    if tail: statements.append(tail)
    return statements

def apply_migrations(connection, migration_dir: Path) -> None:
    migration_dir = Path(migration_dir)
    migration_files = sorted(
        migration_dir.glob("*.sql"),
        key=lambda path: int(path.name.split("_", 1)[0]),
    )

    versions: dict[int, Path] = {}
    for path in migration_files:
        version = int(path.name.split("_", 1)[0])
        if version in versions:
            raise RuntimeError(
                f"Unresolved duplicate migration version {version}: "
                f"{versions[version].name} and {path.name}"
            )
        versions[version] = path

    # Migrations own one transaction boundary. A transaction-scoped advisory
    # lock serializes the entire migration read/apply/publication sequence.
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
        execute("SELECT pg_advisory_xact_lock(hashtext(:lock_key))", {"lock_key": lock_key})
    else:
        execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (lock_key,))

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

            statements = _split_sql_statements(sql)
            if not statements:
                raise RuntimeError(f"migration {path.name} contains no executable SQL")
            for statement in statements:
                execute(statement, static_sql=True)

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

        # Commit atomically publishes the migration history. The transaction-
        # scoped advisory lock is released automatically only after this commit,
        # so a concurrent bootstrap cannot observe a partially published history.
        connection.commit()
    except Exception:
        connection.rollback()
        raise
