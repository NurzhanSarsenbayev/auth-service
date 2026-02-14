from contextlib import asynccontextmanager

from api.v1 import auth, health, oauth, ready, roles, user_roles, users, well_known
from core import telemetry
from core.config import settings
from core.logging import setup_logging
from core.startup_check import validate_runtime_environment
from db.postgres import make_engine, make_session_factory
from db.redis_db import close_redis, init_redis
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi_pagination import add_pagination
from middleware.rate_limit import RateLimiterMiddleware, RateRule
from middleware.request_id import RequestIDMiddleware
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_runtime_environment()

    # --- DB ---
    engine = make_engine()
    session_factory = make_session_factory(engine)

    app.state.engine = engine
    app.state.session_factory = session_factory

    # --- Redis ---
    redis = await init_redis()
    app.state.redis = redis

    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)

    # if settings.database_url.endswith(":app@postgres_auth:5432/auth"):
    #     logger.warning("Running with default development DB credentials.")

    yield

    # --- Shutdown ---
    await engine.dispose()
    await close_redis(redis)


app = FastAPI(title="Auth Service", lifespan=lifespan)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Auth Service",
        version="1.0.0",
        description="API docs",
        routes=app.routes,
    )
    # Add BearerAuth security scheme manually
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
setup_logging(settings.log_format)
if settings.enable_tracer:
    telemetry.setup_tracing("auth_service")
    telemetry.instrument_app(app)
add_pagination(app)
rules = [
    # Signup: stricter
    RateRule(r"^/api/v1/users/signup$", limit=5, window=60),
    # Login: moderate
    RateRule(r"^/api/v1/auth/login$", limit=10, window=60),
    # Everything else: default
    RateRule(
        r"^/api/v1/.*",
        limit=settings.rate_limit_max_requests,
        window=settings.rate_limit_window_sec,
    ),
]

app.add_middleware(
    RateLimiterMiddleware,
    rules=rules,
    default_limit=settings.rate_limit_max_requests,
    default_window=settings.rate_limit_window_sec,
    whitelist_paths=["/api/v1/healthz", "/api/v1/readyz", "/docs", "/openapi.json"],
)
app.add_middleware(RequestIDMiddleware)


# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["roles"])
app.include_router(user_roles.router, prefix="/api/v1/user_roles", tags=["user_roles"])
app.include_router(oauth.router, prefix="/api/v1/oauth", tags=["oauth"])
app.include_router(well_known.router)
app.include_router(health.router, prefix="/api/v1")

app.include_router(ready.router, prefix="/api/v1")
