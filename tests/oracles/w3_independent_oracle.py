from dataclasses import dataclass


@dataclass(frozen=True)
class SchemaOracleResult:
    accepted_upgrade_ids: tuple[str, ...]
    final_version: int
    split_brain: bool
    lost_upgrade: bool
    idempotent_retry_safe: bool


def evaluate_concurrent_upgrades(
    *,
    current_version: int,
    upgrades: tuple[tuple[str, int, int], ...],
) -> SchemaOracleResult:
    """Independent semantic oracle; no GerChain persistence/domain imports.

    Each tuple is (upgrade_id, from_version, to_version). Upgrades compete
    against one canonical predecessor. At most one distinct upgrade may move
    the state from the supplied predecessor; a repeated upgrade ID is an
    idempotent retry only when its transition payload is identical.
    """
    accepted: list[str] = []
    seen: dict[str, tuple[int, int]] = {}
    version = current_version
    lost_upgrade = False
    idempotent_retry_safe = True

    for upgrade_id, from_version, to_version in upgrades:
        transition = (from_version, to_version)
        if upgrade_id in seen:
            # Same identity + same transition is a safe retry; a changed
            # transition under the same identity is not idempotent-safe.
            if seen[upgrade_id] != transition:
                idempotent_retry_safe = False
            continue
        seen[upgrade_id] = transition
        if from_version == version and to_version > from_version:
            accepted.append(upgrade_id)
            version = to_version
        else:
            lost_upgrade = lost_upgrade or from_version == current_version

    return SchemaOracleResult(
        accepted_upgrade_ids=tuple(accepted),
        final_version=version,
        split_brain=len(accepted) > 1 and all(
            from_version == current_version
            for _, from_version, _ in upgrades
        ),
        lost_upgrade=lost_upgrade and len(accepted) == 0,
        idempotent_retry_safe=idempotent_retry_safe,
    )


def stale_predecessor_is_safe(*, current_version: int, from_version: int) -> bool:
    """A decision based on an old predecessor must not become authoritative."""
    return from_version == current_version
