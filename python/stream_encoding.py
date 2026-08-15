"""Shared UTF-8 configuration for PolyAnalyzer process standard streams."""

from __future__ import annotations

import sys


def configure_standard_streams() -> None:
    """Use UTF-8 for redirected streams on every supported platform.

    Windows configures redirected Python streams with the system ANSI code
    page. PolyAnalyzer's JSON and progress output can contain non-ASCII text,
    so pipe consumers must always receive UTF-8 bytes.
    """
    streams = (
        (sys.stdin, "strict"),
        (sys.stdout, "strict"),
        (sys.stderr, "backslashreplace"),
    )
    for stream, errors in streams:
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors=errors)
