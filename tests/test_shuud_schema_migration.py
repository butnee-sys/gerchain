"""SH-16.14 production schema migration tests."""

from sqlalchemy import create_engine, inspect, text, select

from shuud.persistence import CURRENT_SCHEMA_VERSION, SHUUDSchemaVersion, initialize_schema
from shuud.publication_outbox import SHUUDPublicationOutbox


def test_new_database_records_current_schema_version(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'new.db'}", future=True)
    initialize_schema(engine)

    with engine.connect() as connection:
        versions = connection.execute(select(SHUUDSchemaVersion)).fetchall()

    assert versions[-1].version == CURRENT_SCHEMA_VERSION


def test_existing_outbox_database_gets_processing_at_additively(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}", future=True)

    # Simulate the pre-SH-16.13 production schema: the outbox exists but has
    # no processing_at column and contains an already durable publication row.
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE shuud_publication_outbox (
                id INTEGER PRIMARY KEY,
                publication_key VARCHAR(256) NOT NULL UNIQUE,
                status VARCHAR(32) NOT NULL,
                attempts INTEGER NOT NULL,
                last_error TEXT,
                lifecycle_event_json TEXT NOT NULL,
                authorization_json TEXT NOT NULL,
                escrow_json TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                published_at TIMESTAMP
            )
        """))
        connection.execute(text("""
            INSERT INTO shuud_publication_outbox
            (id, publication_key, status, attempts, last_error,
             lifecycle_event_json, authorization_json, escrow_json, created_at)
            VALUES
            (1, 'AUTH-LEGACY', 'PUBLISHED', 1, NULL, '{}', '{}', '{}', CURRENT_TIMESTAMP)
        """))

    initialize_schema(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("shuud_publication_outbox")}
    assert "processing_at" in columns

    with engine.connect() as connection:
        row = connection.execute(
            select(SHUUDPublicationOutbox).where(
                SHUUDPublicationOutbox.publication_key == "AUTH-LEGACY"
            )
        ).one()

    assert row.status == "PUBLISHED"
    assert row.attempts == 1
    assert row.processing_at is None


def test_schema_migration_is_idempotent(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'repeat.db'}", future=True)
    initialize_schema(engine)
    initialize_schema(engine)
    initialize_schema(engine)

    with engine.connect() as connection:
        versions = connection.execute(select(SHUUDSchemaVersion)).fetchall()

    assert [row.version for row in versions] == [CURRENT_SCHEMA_VERSION]
