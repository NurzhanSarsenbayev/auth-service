from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.health import router as health_router


def test_healthz_ok():
    app = FastAPI()
    app.include_router(health_router, prefix="/api/v1")
    client = TestClient(app)

    r = client.get("/api/v1/healthz")

    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
