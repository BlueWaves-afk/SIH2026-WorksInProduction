"""Dedicated background-jobs entrypoint.

Run this as a separate Render *worker* service so the ingest -> rescore ->
outreach loop and the officer digest do not depend on the web dyno being awake
(free web dynos sleep). When a worker owns the jobs, set
``ENABLE_BACKGROUND_JOBS=false`` on the web service so the cycle is not run
twice.

    python -m app.worker
"""

from __future__ import annotations

import signal
import threading

import structlog

from app.outreach.scheduler import start_scheduler

logger = structlog.get_logger()


def main() -> None:
    scheduler = start_scheduler()
    logger.info("worker_started")
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    try:
        stop.wait()
    finally:
        scheduler.shutdown(wait=False)
        logger.info("worker_stopped")


if __name__ == "__main__":
    main()
