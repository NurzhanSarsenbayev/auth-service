import contextvars
import json
import logging
from datetime import UTC, datetime
from typing import Any

# Public API used by middleware: request_id_ctx.set(...) / .get(...)
request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


class JsonFormatter(logging.Formatter):
    """Minimal JSON formatter for production-friendly logs.

    Fields:
      - ts: ISO8601 UTC timestamp
      - level: log level name
      - logger: logger name
      - message: formatted log message
      - request_id: request correlation id (if available)
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        rid = getattr(record, "request_id", None)
        if rid:
            payload["request_id"] = rid

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def setup_logging(log_format: str = "text") -> None:
    """Configure application logger.

    log_format:
      - "text" (default): human-readable logs
      - "json": one-line JSON per record
    """
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False  # prevent duplicate logs via root/uvicorn

    # Reset handlers to avoid duplication on reloads/tests
    app_logger.handlers.clear()

    handler = logging.StreamHandler()

    if (log_format or "text").lower() == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s | request_id=%(request_id)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    handler.addFilter(RequestIdFilter())
    app_logger.addHandler(handler)
