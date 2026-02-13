import redis.asyncio as redis
from core.config import settings
from fastapi import Request


async def init_redis() -> redis.Redis:
    host = settings.redis_host
    port = settings.redis_port

    client = redis.from_url(
        f"redis://{host}:{port}/0",
        encoding="utf-8",
        decode_responses=True,
    )
    await client.ping()
    return client


async def close_redis(client: redis.Redis) -> None:
    if client:
        await client.close()


# 👇 зависимость для FastAPI
async def get_redis(request: Request) -> redis.Redis:
    return request.app.state.redis
