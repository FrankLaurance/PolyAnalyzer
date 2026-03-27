"""Entry point for the PolyAnalyzer JSON-RPC sidecar process."""

from __future__ import annotations

import logging
import signal
import sys


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


def main() -> None:
    _setup_logging()
    logger = logging.getLogger(__name__)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("PolyAnalyzer sidecar starting")

    from api import serve  # noqa: WPS433 – deferred import after logging setup

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
