import redis
from src.config import app_config as config

async def get_redis() -> redis.asyncio.Redis:

    return redis.asyncio.from_url(
        config.settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
