import logging

import pytest

from core.logging import request_id_ctx, setup_logging


@pytest.mark.unit
def test_text_logging_contains_request_id(capsys):
    setup_logging(log_format="text")
    logger = logging.getLogger("app")

    token = request_id_ctx.set("rid-xyz")
    try:
        logger.info("hello")
    finally:
        request_id_ctx.reset(token)

    captured = capsys.readouterr()
    out = captured.err  # StreamHandler() -> stderr
    assert "hello" in out
    assert "request_id=rid-xyz" in out
