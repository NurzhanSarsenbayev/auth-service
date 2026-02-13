import logging
import re
import time
import uuid
from collections.abc import Iterable

from core.config import settings
from core.logging import request_id_ctx
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse


def _client_ip(request: Request) -> str:
    # Trust X-Forwarded-For only when service is behind a trusted proxy
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateRule:
    __slots__ = ("pattern", "limit", "window")

    def __init__(self, pattern: str, limit: int, window: int):
        self.pattern = re.compile(pattern)
        self.limit = limit
        self.window = window  # сек


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Sliding window на Redis: на ключе ZSET храним таймстемпы запросов в окне.
    Алгоритм (на каждый запрос):
      1) ZREMRANGEBYSCORE(key, 0, now-window)
      2) ZCARD(key) -> count
      3) Если count >= limit -> 429
         (берём самый старый ts, считаем reset и Retry-After)
      4) Иначе ZADD(now, member), EXPIRE(key, window)
    Заголовки: X-RateLimit-Limit, X-RateLimit-Remaining,
     X-RateLimit-Reset(+ Retry-After при 429).
    Идентификатор: user_id, если он известен в request.state.user_id; иначе IP.
    """

    def __init__(
        self,
        app,
        rules: Iterable[RateRule] | None = None,
        default_limit: int = None,
        default_window: int = None,
        whitelist_paths: Iterable[str] | None = None,
    ):
        super().__init__(app)
        self.logger = logging.getLogger("app")

        self.default_limit = default_limit or settings.rate_limit_max_requests
        self.default_window = default_window or settings.rate_limit_window_sec

        # правила: от более специфичных к более общим
        self.rules = list(rules or [])
        self.whitelist = set(whitelist_paths or ["/health", "/metrics"])

    def _pick_rule(self, path: str) -> RateRule:
        for r in self.rules:
            if r.pattern.match(path):
                return r
        # дефолт
        return RateRule(pattern=r".*", limit=self.default_limit, window=self.default_window)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # если в тестах — пропускаем без лимитов
        if getattr(settings, "testing", False):
            return await call_next(request)

        # белый список путей — пропускаем без лимита
        if request.url.path in self.whitelist:
            return await call_next(request)

        rule = self._pick_rule(request.url.path)

        # определяем "субъект" лимита
        subject = getattr(getattr(request, "state", object()), "user_id", None)
        if subject:
            ident = f"user:{subject}"
        else:
            ident = f"ip:{_client_ip(request)}"

        key = f"rl:{rule.limit}:{rule.window}:{ident}:{request.url.path}"
        now_ms = int(time.time() * 1000)
        win_ms = rule.window * 1000

        redis = request.app.state.redis

        # Sliding window: удаляем старые, считаем, решаем.
        # Используем пайплайн для минимизации RTT.
        pipe = redis.pipeline(transaction=False)
        pipe.zremrangebyscore(key, 0, now_ms - win_ms)
        pipe.zcard(key)
        try:
            _, count = await pipe.execute()
        except Exception as e:
            # Если Redis недоступен — graceful degradation
            req_id = request_id_ctx.get("-")
            self.logger.warning(f"[rate] Redis error, skip limiting (req_id={req_id}): {e}")
            return await call_next(request)

        if count >= rule.limit:
            # берём самый старый таймстемп, чтобы понять когда окно освободится
            oldest = await redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_ts_ms = int(oldest[0][1])
                reset_epoch = (oldest_ts_ms + win_ms) // 1000
                retry_after = max(0, reset_epoch - int(now_ms // 1000))
            else:
                reset_epoch = int((now_ms + win_ms) // 1000)
                retry_after = rule.window

            headers = {
                "X-RateLimit-Limit": str(rule.limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_epoch),
                "Retry-After": str(retry_after),
            }
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests"},
                headers=headers,
            )

        # ещё не достигли лимита — фиксируем текущий запрос
        member = f"{now_ms}-{uuid.uuid4().hex}"
        pipe = redis.pipeline(transaction=False)
        pipe.zadd(key, {member: now_ms})
        pipe.expire(key, rule.window)  # чтобы ключи не накапливались
        pipe.zcard(key)  # получим новое значение count
        _, _, new_count = await pipe.execute()
        remaining = max(0, rule.limit - int(new_count))

        # проксируем дальше
        response = await call_next(request)

        # добавим rate заголовки в ответ
        # reset = момент, когда самый ранний элемент выпадет из окна
        oldest = await redis.zrange(key, 0, 0, withscores=True)
        if oldest:
            oldest_ts_ms = int(oldest[0][1])
            reset_epoch = (oldest_ts_ms + win_ms) // 1000
        else:
            reset_epoch = int((now_ms + win_ms) // 1000)

        response.headers["X-RateLimit-Limit"] = str(rule.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_epoch)
        return response
