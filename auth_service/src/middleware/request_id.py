import logging
import uuid

from core.logging import request_id_ctx
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request_id_ctx.set(request_id)

        logger.info(f"Request {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"Response {response.status_code}")

        response.headers["x-request-id"] = request_id
        return response
