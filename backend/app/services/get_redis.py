import redis.asyncio as aioredis
from app.core.config import settings

from redis import Redis


def get_redis() -> Redis:
    use_tls = settings.REDIS_PORT == 6150

    redis_kwargs = {
        "host": settings.REDIS_HOST,
        "port": settings.REDIS_PORT,
        "password": settings.REDIS_PASSWORD,
        "decode_responses": True,
        "socket_timeout": 15.0,
    }

    if use_tls:
        redis_kwargs.update({"ssl": True, "ssl_cert_reqs": "none"})

    return Redis(**redis_kwargs)


def get_async_redis() -> aioredis.Redis:
    use_tls = settings.REDIS_PORT == 6150

    redis_kwargs = {
        "host": settings.REDIS_HOST,
        "port": settings.REDIS_PORT,
        "password": settings.REDIS_PASSWORD,
        "decode_responses": True,
        "socket_timeout": 15.0,
    }

    if use_tls:
        redis_kwargs.update({"ssl": True, "ssl_cert_reqs": "none"})

    return aioredis.Redis(**redis_kwargs)
