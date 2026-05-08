import redis
from src.config import app_config as config

redis_client: redis.asyncio.Redis | None = None


async def get_redis() -> redis.asyncio.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.asyncio.from_url(
            config.settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return redis_client
