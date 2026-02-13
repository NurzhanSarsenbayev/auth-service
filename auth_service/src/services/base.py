from redis.asyncio import Redis

CACHE_KEY = "user_roles:{}"


class BaseService:
    def __init__(self, repo, redis: Redis | None = None):
        self.repo = repo
        self.redis = redis

    async def get_cached_list(self, key: str) -> list[str] | None:
        if self.redis:
            cached = await self.redis.smembers(key)
            if cached:
                return [c.decode() if isinstance(c, bytes) else c for c in cached]
        return None

    async def set_cache_list(self, key: str, values: list[str]):
        if self.redis and values:
            await self.redis.sadd(key, *values)
