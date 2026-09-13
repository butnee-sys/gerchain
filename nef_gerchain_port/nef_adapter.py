"""NEF implementation adapter.

NEF internals remain unchanged. This adapter is the only place where the
external boundary reaches NEF state engines.
"""

from network.nef_engine import NEFStateEngine as NEFEngine
from network.nef_state_engine import NEFStateEngine

__all__ = ["NEFEngine", "NEFStateEngine"]
