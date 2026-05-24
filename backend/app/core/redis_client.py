from functools import lru_cache

from redis import Redis
from rq import Queue

from app.core.config import settings

QUEUE_NAME = "default"


@lru_cache
def get_redis() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=False)


@lru_cache
def get_queue() -> Queue:
    return Queue(QUEUE_NAME, connection=get_redis())


def ping_redis() -> None:
    get_redis().ping()
