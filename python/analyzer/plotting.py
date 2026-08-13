"""Shared plotting setup for analyzer modules."""

from __future__ import annotations

import logging
import threading
from typing import Any

_PLOT_LOCK = threading.Lock()
_PLOT_MODULE: Any | None = None


def configure_plotting() -> Any:
    """Import and configure matplotlib once per sidecar process."""
    global _PLOT_MODULE
    if _PLOT_MODULE is not None:
        return _PLOT_MODULE

    with _PLOT_LOCK:
        if _PLOT_MODULE is not None:
            return _PLOT_MODULE

        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        plt.rcParams["font.sans-serif"] = [
            "PingFang SC",
            "Hiragino Sans GB",
            "Arial Unicode MS",
            "Noto Sans CJK SC",
            "DejaVu Sans",
        ]
        plt.rcParams["axes.unicode_minus"] = False
        _PLOT_MODULE = plt
        return _PLOT_MODULE


def warm_plotting(logger: logging.Logger | None = None) -> None:
    """Warm up matplotlib without raising into the caller."""
    try:
        configure_plotting()
        if logger:
            logger.info("Plot engine warmed")
    except Exception as exc:
        if logger:
            logger.warning("Plot engine warmup failed: %s", exc)
