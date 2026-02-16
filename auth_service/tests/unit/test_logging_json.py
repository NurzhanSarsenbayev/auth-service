import json
import logging

import pytest

from core.logging import request_id_ctx, setup_logging


@pytest.mark.unit
def test_json_logging_includes_request_id_and_exc_info(capsys):
    setup_logging(log_format="json")
    logger = logging.getLogger("app")

    token = request_id_ctx.set("rid-123")
    try:
        try:
            raise ValueError("boom")
        except ValueError:
            logger.exception("something failed")
    finally:
        request_id_ctx.reset(token)

    # StreamHandler() defaults to stderr
    captured = capsys.readouterr()
    out = captured.err.strip()
    assert out, f"Expected log output on stderr, got out={captured.out!r}, err={captured.err!r}"

    payload = json.loads(out)
    assert payload["level"] == "ERROR"
    assert payload["logger"] == "app"
    assert payload["message"] == "something failed"
    assert payload["request_id"] == "rid-123"
    assert "exc_info" in payload
    assert "ValueError" in payload["exc_info"]
