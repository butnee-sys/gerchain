    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: migrate(), range(2)))

    with connect() as conn:
        rows = conn.execute("SELECT version, checksum FROM schema_version ORDER BY version").fetchall()
        versions = [row[0] for row in rows]\n        assert versions\n        assert versions == list(range(1, len(versions) + 1))
        assert len(rows[0][1]) == 64


def test_migration_checksum_mismatch_is_rejected(tmp_path):
    with connect() as conn: