"""RQ worker entrypoint. Run as `python -m app.jobs.worker`."""

from __future__ import annotations

import logging

from rq import Worker

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.redis_client import QUEUE_NAME, get_queue, get_redis

setup_logging()
logger = logging.getLogger("app.jobs.worker")


def enqueue(func_path: str, *args, **kwargs):
    """Helper for routes to enqueue jobs by dotted path."""
    queue = get_queue()
    return queue.enqueue(func_path, *args, **kwargs)


def main() -> None:
    if not settings.USE_REDIS_QUEUE:
        logger.info("USE_REDIS_QUEUE is false, exiting.")
        return

    redis = get_redis()
    logger.info(
        "Starting RQ worker on queue=%s redis=%s", QUEUE_NAME, settings.REDIS_URL
    )
    worker = Worker([get_queue()], connection=redis)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
