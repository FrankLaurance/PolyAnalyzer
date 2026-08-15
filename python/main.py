"""Entry point for the PolyAnalyzer JSON-RPC sidecar process."""

from __future__ import annotations

import logging
import os
import signal
import sys
import tempfile
import threading
import time


_CACHE_ROOT = os.path.join(tempfile.gettempdir(), "polyanalyzer-cache")
_MPL_CACHE_DIR = os.path.join(_CACHE_ROOT, "matplotlib")
_XDG_CACHE_DIR = os.path.join(_CACHE_ROOT, "xdg")
os.makedirs(_MPL_CACHE_DIR, exist_ok=True)
os.makedirs(_XDG_CACHE_DIR, exist_ok=True)
os.environ["MPLCONFIGDIR"] = _MPL_CACHE_DIR
os.environ["XDG_CACHE_HOME"] = _XDG_CACHE_DIR


def _configure_standard_streams() -> None:
    """Use UTF-8 for the JSON-RPC pipes on every platform.

    Windows configures redirected Python streams with the system ANSI code
    page. Tauri's shell plugin decodes sidecar output as UTF-8, so any Chinese
    progress or log message would otherwise break the transport.
    """
    streams = (
        (sys.stdin, "strict"),
        (sys.stdout, "strict"),
        (sys.stderr, "backslashreplace"),
    )
    for stream, errors in streams:
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors=errors)


def _setup_logging() -> None:
    """Configure logging to stderr so stdout stays clean for JSON-RPC."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )


def _handle_signal(signum: int, _frame: object) -> None:
    logging.getLogger(__name__).info("Received signal %d, shutting down", signum)
    sys.exit(0)


def _notify_warmup(progress: float, message: str) -> None:
    """Emit a warmup status notification for the frontend banner."""
    from api import send_notification

    send_notification(
        "progress",
        {"warmup": True, "progress": progress, "message": message},
    )


def _warm_runtime_async(logger: logging.Logger, delay: float = 3.0) -> None:
    """Warm slow analyzer imports after the sidecar is ready."""

    def target() -> None:
        time.sleep(delay)
        _notify_warmup(0.0, "引擎预热中…")
        try:
            from analyzer.mw import MolecularWeightAnalyzer  # noqa: F401,WPS433
            from analyzer.plotting import warm_plotting  # noqa: WPS433

            warm_plotting(logger)
            logger.info("MW runtime warmed")
            _notify_warmup(100.0, "引擎预热完成")
        except Exception as exc:
            logger.warning("Runtime warmup failed: %s", exc)
            _notify_warmup(100.0, "引擎预热失败")

    threading.Thread(target=target, name="runtime-warmup", daemon=True).start()


def main() -> None:
    _configure_standard_streams()
    _setup_logging()
    logger = logging.getLogger(__name__)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("PolyAnalyzer sidecar starting")

    from api import serve  # noqa: WPS433 – deferred import after logging setup

    _warm_runtime_async(logger)

    try:
        serve()
    except SystemExit:
        pass
    except Exception:
        logger.exception("Sidecar crashed")
        sys.exit(1)
    finally:
        logger.info("PolyAnalyzer sidecar exiting")


if __name__ == "__main__":
    main()
