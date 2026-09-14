"""Standalone SHUUD application entrypoint.

SHUUD is a separate application product. It uses the NEF–GerChain ecosystem
through its application-layer integration, but its web server must not host the
GerChain dashboard as its root application.
"""

from .app import app

__all__ = ["app"]
