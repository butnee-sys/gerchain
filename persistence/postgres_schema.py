from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine


_SCHEMA_DIR = Path(__file__).resolve().parents[1] / "postgres" / "schema"


def _statements(sql: str) -> list[str]:
    return [part.strip() for part in sql.split(";") if part.strip()]


def apply_postgres_schema(engine: Engine) -> None:
    """Apply ordered SQL migrations exactly once.

    The runner is intentionally PostgreSQL-only and records the SHA-256 of each
    applied migration. A changed migration version fails closed instead of
    silently rewriting production schema history.
    """
    if engine.dialect.name != "postgresql":
        raise ValueError("production schema migration requires PostgreSQL")

    migrations = sorted(_SCHEMA_DIR.glob("*.sql"))
    if not migrations:
        raise RuntimeError(f"no PostgreSQL migrations found in {_SCHEMA_DIR}")

    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_version ("
                "version BIGINT PRIMARY KEY, checksum TEXT NOT NULL, "
                "applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            )
        )

        for migration in migrations:
            try:
                version = int(migration.stem.split("_", 1)[0])
            except (ValueError, IndexError) as exc:
                raise RuntimeError(f"invalid migration filename: {migration.name}") from exc

            sql = migration.read_text(encoding="utf-8")
            checksum = sha256(sql.encode("utf-8")).hexdigest()
            existing = connection.execute(
                text("SELECT checksum FROM schema_version WHERE version = :version"),
                {"version": version},
            ).scalar_one_or_none()

            if existing is not None:
                if existing != checksum:
                    raise RuntimeError(
                        f"migration {migration.name} checksum mismatch; refusing to continue"
                    )
                continue

            for statement in _statements(sql):
                connection.exec_driver_sql(statement)

            connection.execute(
                text(
                    "INSERT INTO schema_version(version, checksum) "
                    "VALUES (:version, :checksum)"
                ),
                {"version": version, "checksum": checksum},
            )
