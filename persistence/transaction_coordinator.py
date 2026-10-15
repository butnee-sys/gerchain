from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import Session


class AtomicTransactionCoordinator:
    """Owns the outer DB transaction, but no domain authority.

    Ledger, Escrow, Witness and Outbox components participate in the supplied
    session. The coordinator is the only component in this boundary that
    commits or rolls back the business transaction.
    """

    def __init__(self, session_factory):
        self.session_factory = session_factory

    @contextmanager
    def transaction(self) -> Iterator[Session]:
        with self.session_factory() as session:
            try:
                with session.begin():
                    yield session
            except Exception:
                session.rollback()
                raise


__all__ = ["AtomicTransactionCoordinator"]
