"""Shared plotting setup for analyzer modules."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

_PLOT_LOCK = threading.Lock()
_PLOT_MODULE: Any | None = None
_WARMUP_STARTED = False


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


def warm_plotting_async(logger: logging.Logger | None = None, delay: float = 0.0) -> None:
    """Start one background matplotlib warmup for the sidecar process."""
    global _WARMUP_STARTED
    if _WARMUP_STARTED:
        return
    _WARMUP_STARTED = True

    def target() -> None:
        if delay > 0:
            time.sleep(delay)
        warm_plotting(logger)

    thread = threading.Thread(
        target=target,
        name="plot-engine-warmup",
        daemon=True,
    )
    thread.start()
