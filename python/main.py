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


def _warm_runtime_async(logger: logging.Logger, delay: float = 3.0) -> None:
    """Warm slow analyzer imports after the sidecar is ready."""

    def target() -> None:
        time.sleep(delay)
        try:
            from analyzer.mw import MolecularWeightAnalyzer  # noqa: F401,WPS433
            from analyzer.plotting import warm_plotting  # noqa: WPS433

            warm_plotting(logger)
            logger.info("MW runtime warmed")
        except Exception as exc:
            logger.warning("Runtime warmup failed: %s", exc)

    threading.Thread(target=target, name="runtime-warmup", daemon=True).start()


def main() -> None:
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
