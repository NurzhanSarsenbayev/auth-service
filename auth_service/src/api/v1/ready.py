import asyncio
import logging
import socket

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

logger = logging.getLogger("app")
router = APIRouter(tags=["ready"])


def _tcp_check_sync(host: str, port: int, timeout: float) -> None:
    """Fast TCP dial check (no Redis protocol)."""
    with socket.create_connection((host, port), timeout=timeout):
        return


@router.get("/readyz")
async def readiness(request: Request) -> JSONResponse:
    """Readiness probe: checks critical dependencies (Postgres + Redis).

    Returns:
      - 200 if DB and Redis are reachable
      - 503 otherwise
    """
    details: dict[str, str] = {}

    # 1) Postgres check
    try:
        session_factory = getattr(request.app.state, "session_factory", None)
        if session_factory is None:
            raise RuntimeError("db session_factory is not initialized")

        async with session_factory() as session:
            await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=1.0)

        details["postgres"] = "ok"
    except Exception as exc:  # noqa: BLE001 - readiness must never raise
        logger.warning("readiness check failed: postgres: %r", exc)
        details["postgres"] = "error"

    # 2) Redis check (sync TCP dial in thread to avoid asyncio DNS cancellation warnings)
    try:
        redis = getattr(request.app.state, "redis", None)
        if redis is None:
            raise RuntimeError("redis client is not initialized")

        kwargs = getattr(redis.connection_pool, "connection_kwargs", {}) or {}
        host = kwargs.get("host", "redis")
        port = int(kwargs.get("port", 6379))

        await asyncio.to_thread(_tcp_check_sync, host, port, 0.5)
        details["redis"] = "ok"

    except TimeoutError:
        logger.warning("readiness check failed: redis: timeout")
        details["redis"] = "error"

    except OSError as exc:
        # Includes gaierror, connection refused, etc.
        logger.warning("readiness check failed: redis: %r", exc)
        details["redis"] = "error"

    except Exception as exc:  # noqa: BLE001
        logger.warning("readiness check failed: redis: %r", exc)
        details["redis"] = "error"

    is_ready = all(v == "ok" for v in details.values())

    if is_ready:
        return JSONResponse(status_code=200, content={"status": "ready", "details": details})

    return JSONResponse(status_code=503, content={"status": "not_ready", "details": details})
