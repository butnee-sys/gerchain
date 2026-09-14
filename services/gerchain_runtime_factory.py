from __future__ import annotations

from typing import Any, Callable

from sqlalchemy import Engine

from persistence.atomic_release import initialize_atomic_release_schema
from services.gerchain_runtime import GerchainRuntime


class ProductionRuntimeFactory:
    """Create the production GerChain runtime with PostgreSQL as authority."""

    @staticmethod
    def create(
        *,
        escrow_id: str,
        amount: int,
        currency: str,
        witness_id: str,
        engine: Engine,
        session_factory: Callable[[], Any],
        initial_state: dict[str, Any] | None = None,
        manifest: dict[str, Any] | None = None,
        initial_money_state: dict[str, Any] | None = None,
    ) -> GerchainRuntime:
        if engine is None or session_factory is None:
            raise ValueError("production runtime requires PostgreSQL engine and session factory")
        initialize_atomic_release_schema(engine)
        runtime = GerchainRuntime(
            escrow_id=escrow_id,
            amount=amount,
            currency=currency,
            witness_id=witness_id,
            initial_state=initial_state,
            manifest=manifest,
            initial_money_state=initial_money_state,
        )
        runtime.configure_postgres_release(session_factory)
        runtime.runtime_mode = "production-postgresql"
        return runtime


__all__ = ["ProductionRuntimeFactory"]
