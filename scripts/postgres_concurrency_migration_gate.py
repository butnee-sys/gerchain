from __future__ import annotations

import concurrent.futures
import hashlib
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ["GERCHAIN_TEST_DATABASE_URL"]
MIGRATION = Path("postgres/schema/001_concurrency.sql")
VARIANTS = range(1, 17)


def connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def run_migration(sql: str) -> None:
    # The migration contains multiple DDL statements and is intentionally executed
    # as one script by psycopg's simple-query path (no bound parameters).
    with connect() as conn:
        conn.execute(sql)


def digest_rows(conn, query: str, params=()) -> str:
    rows = conn.execute(query, params).fetchall()
    canonical = "\n".join(
        repr(tuple(row.values())) for row in rows
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def insert_race(variant: int, worker: int) -> None:
    # Independent function call => independent PostgreSQL connection.
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO gate_concurrency_probe(variant, worker, payload)
            VALUES (%s, %s, %s)
            ON CONFLICT (variant) DO NOTHING
            """,
            (variant, worker, f"variant-{variant}"),
        )


def main() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    migration_checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()

    run_migration(sql)

    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gate_concurrency_probe (
                variant INTEGER PRIMARY KEY CHECK (variant BETWEEN 1 AND 16),
                worker INTEGER NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO schema_version(version, checksum)
            VALUES (1, %s)
            ON CONFLICT (version) DO NOTHING
            """,
            (migration_checksum,),
        )
        stored = conn.execute(
            "SELECT checksum FROM schema_version WHERE version = 1"
        ).fetchone()["checksum"]
        if stored != migration_checksum:
            raise AssertionError(
                f"migration checksum drift: stored={stored}, current={migration_checksum}"
            )

        # Seed non-empty canonical rows so migration replay proves preservation
        # of actual schema data, not only stability of empty-table fingerprints.
        conn.execute("""
            INSERT INTO escrows
                (id, sender_address, receiver_address, amount, state, condition_desc,
                 updated_at, refund_destination, currency, version, created_at)
            VALUES
                ('gate-escrow', 'gate-source', 'gate-beneficiary', 17, 'CREATED',
                 'migration-gate-fixture', now(), 'gate-source', 'MNT', 0, now())
            ON CONFLICT (id) DO NOTHING
        """)
        conn.execute("""
            INSERT INTO gerchain_ledger_accounts
                (account_id, currency, balance, version, updated_at)
            VALUES ('gate-account', 'MNT', 1700, 0, now())
            ON CONFLICT (account_id) DO NOTHING
        """)
        conn.execute("""
            INSERT INTO gerchain_ledger_movements
                (transaction_id, source, destination, amount, currency, operation,
                 escrow_id, integrity_hash, created_at)
            VALUES
                ('gate-movement', 'gate-source', 'gate-beneficiary', 17, 'MNT',
                 'SETTLEMENT', 'gate-escrow', 'gate-integrity-hash', now())
            ON CONFLICT (transaction_id) DO NOTHING
        """)

    # 32 competing inserts (two independent connections per variant) must leave
    # exactly one authoritative row for each of variants 1..16.
    jobs = [(variant, worker) for variant in VARIANTS for worker in (1, 2)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(insert_race, variant, worker) for variant, worker in jobs]
        for future in futures:
            future.result()

    with connect() as conn:
        variants = conn.execute(
            "SELECT variant, count(*) AS n FROM gate_concurrency_probe "
            "GROUP BY variant ORDER BY variant"
        ).fetchall()
        expected = [(v, 1) for v in VARIANTS]
        actual = [(row["variant"], row["n"]) for row in variants]
        if actual != expected:
            raise AssertionError(f"variants must each have exactly one row: {actual}")

        # Record stable data fingerprints before replaying the migration.
        before_probe = digest_rows(
            conn,
            "SELECT variant, worker, payload FROM gate_concurrency_probe ORDER BY variant",
        )
        before_escrows = digest_rows(
            conn,
            "SELECT id, sender_address, receiver_address, amount::text, state, "
            "condition_desc, updated_at, refund_destination, currency, version, created_at "
            "FROM escrows ORDER BY id",
        )
        before_accounts = digest_rows(
            conn,
            "SELECT account_id, currency, balance, version, updated_at "
            "FROM gerchain_ledger_accounts ORDER BY account_id",
        )
        before_movements = digest_rows(
            conn,
            "SELECT transaction_id, source, destination, amount, currency, operation, "
            "escrow_id, integrity_hash, created_at FROM gerchain_ledger_movements "
            "ORDER BY transaction_id",
        )

    # Idempotency gate: apply the exact same migration again.
    run_migration(sql)

    with connect() as conn:
        after_probe = digest_rows(
            conn,
            "SELECT variant, worker, payload FROM gate_concurrency_probe ORDER BY variant",
        )
        after_escrows = digest_rows(
            conn,
            "SELECT id, sender_address, receiver_address, amount::text, state, "
            "condition_desc, updated_at, refund_destination, currency, version, created_at "
            "FROM escrows ORDER BY id",
        )
        after_accounts = digest_rows(
            conn,
            "SELECT account_id, currency, balance, version, updated_at "
            "FROM gerchain_ledger_accounts ORDER BY account_id",
        )
        after_movements = digest_rows(
            conn,
            "SELECT transaction_id, source, destination, amount, currency, operation, "
            "escrow_id, integrity_hash, created_at FROM gerchain_ledger_movements "
            "ORDER BY transaction_id",
        )
        stored = conn.execute(
            "SELECT checksum FROM schema_version WHERE version = 1"
        ).fetchone()["checksum"]

    if stored != migration_checksum:
        raise AssertionError("stored migration checksum changed after replay")
    if (before_probe, before_escrows, before_accounts, before_movements) != (
        after_probe, after_escrows, after_accounts, after_movements
    ):
        raise AssertionError("data fingerprint changed after re-running migration")

    print(f"PASS migration_sha256={migration_checksum}")
    print("PASS PostgreSQL independent connections: 2 per variant")
    print("PASS variants 1..16: exactly one row each")
    print("PASS schema_version checksum stable across migration replay")
    print("PASS probe, escrow, ledger-account, and ledger-movement fingerprints unchanged")


if __name__ == "__main__":
    main()
