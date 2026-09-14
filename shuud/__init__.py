"""Legacy import facade for the independent SHUUD application.

Product implementation lives exclusively under ``apps.shuud``. This package
exists only to preserve existing integrations while callers migrate to the
explicit ``apps.shuud`` namespace.
"""

from pathlib import Path

__path__ = [str(Path(__file__).resolve().parent.parent / "apps" / "shuud")]
