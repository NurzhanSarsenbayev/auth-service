import contextvars
import logging

request_id_ctx = contextvars.ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx.get()
        return True


def setup_logging():
    log_format = "%(asctime)s | %(levelname)s | %(name)s | req_id=%(request_id)s | %(message)s"

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(log_format))
    handler.addFilter(RequestIdFilter())

    app_logger = logging.getLogger("app")  # 👈 отдельный логгер
    app_logger.setLevel(logging.INFO)
    app_logger.addHandler(handler)
    app_logger.propagate = False  # 👈 чтобы не уходило в root/uvicorn

    return app_logger
