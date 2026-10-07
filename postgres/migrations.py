                        version BIGINT PRIMARY KEY,
                        checksum TEXT NOT NULL,
                        applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """,
                )
            # Defensive table-level barrier for legacy migration runners that do not honor the advisory lock.
            _execute(conn, "LOCK TABLE schema_version IN ACCESS EXCLUSIVE MODE")
            rows = _execute(
                conn,
                "SELECT version, checksum FROM schema_version ORDER BY version",
            ).fetchall()
            applied = {int(row[0]): row[1] for row in rows}

            for version in sorted(preferred):
                migration = preferred[version]
                sql = migration.read_text(encoding="utf-8")
                digest = checksum(sql)
                accepted_digests = set(LEGACY_CHECKSUMS.get(version, set()))
                accepted_digests.update(FROZEN_CHECKSUMS.get(version, set()))

                if version in applied:
                    if applied[version] != digest and applied[version] not in accepted_digests:
                        raise RuntimeError(
                            f"Migration checksum mismatch for version {version}: "
                            f"applied={applied[version]} expected={digest}"
                        )
                    continue

                migration_sql = sql.replace("BEGIN;", "").replace("COMMIT;", "")
                _execute(conn, migration_sql)
                # Concurrent runners must never publish duplicate schema history.
                # The unique version key is a final publication barrier even if
                # an older runner reaches this point after the advisory lock path.
                # The transaction-scoped advisory lock serializes compliant runners;
                # ON CONFLICT remains a second-line idempotency barrier for legacy
                # or differently-versioned bootstrap callers.
                _execute(
                    conn,
                    """
                    INSERT INTO schema_version(version, checksum)
                    VALUES (%s, %s)
                    ON CONFLICT (version) DO NOTHING
                    """,
                    (version, digest),