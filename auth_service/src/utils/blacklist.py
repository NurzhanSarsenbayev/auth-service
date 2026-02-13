import redis.asyncio as redis
from utils.tokens import decode_token, get_token_ttl


class TokenBlacklist:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def add(self, token: str):
        """Заблокировать refresh-токен до истечения"""
        payload = decode_token(token)
        jti = payload.get("jti")
        if not jti:
            return
        ttl = get_token_ttl(token)
        if ttl > 0:
            await self.redis.setex(f"blacklist:{jti}", ttl, "1")

    async def exists(self, token: str) -> bool:
        """Проверить, заблокирован ли токен"""
        payload = decode_token(token)
        jti = payload.get("jti")
        if not jti:
            return True
        return await self.redis.exists(f"blacklist:{jti}") == 1
