"""
RQ worker entrypoint.
Run: python -m worker.rq_worker
Requires Redis.
"""
import os
from redis import Redis
from rq import Worker, Queue, Connection
from app.core.config import get_settings

settings = get_settings()
redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
redis_conn = Redis.from_url(redis_url)
listen = ["reports"]

if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
