from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_user: str = ""
    db_password: str = ""
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = ""

    jwt_algorithm: str = "RS256"
    jwt_private_key_path: str = ""
    jwt_public_key_path: str = ""

    @property
    def jwt_private_key(self) -> str:
        with open(self.jwt_private_key_path, encoding="utf-8") as f:
            return f.read()

    @property
    def jwt_public_key(self) -> str:
        with open(self.jwt_public_key_path, encoding="utf-8") as f:
            return f.read()

    redis_host: str = "localhost"
    redis_port: int = 6379

    yandex_client_id: str | None = None
    yandex_client_secret: str | None = None
    yandex_redirect_uri: str | None = None

    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str | None = None

    # OpenTelemetry / Jaeger
    otel_sampling_ratio: float = 1.0
    otel_service_name: str = "auth-service"
    otel_service_version: str = "0.1.0"
    otel_environment: str = "local"
    otel_exporter_otlp_endpoint: str | None = None

    testing: bool = False  # Test-mode switch
    enable_tracer: bool = False
    cookie_secure: bool = False

    # Logging: "text" (default) or "json"
    log_format: str = "text"

    rate_limit_window_sec: int = 60
    rate_limit_max_requests: int = 100

    # Trust proxy headers (X-Forwarded-For, etc.) ONLY behind a trusted reverse proxy.
    # If service is exposed directly, keep this False to avoid spoofing.
    trust_proxy_headers: bool = False

    # Connection timeouts (app-level, not only entrypoint)
    db_connect_timeout_sec: int = 10
    redis_connect_timeout_sec: int = 5
    redis_socket_timeout_sec: int = 5

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @model_validator(mode="after")
    def validate_required(self):
        required = [
            ("db_user", self.db_user),
            ("db_password", self.db_password),
            ("db_name", self.db_name),
            ("jwt_private_key_path", self.jwt_private_key_path),
            ("jwt_public_key_path", self.jwt_public_key_path),
        ]
        missing = [name for name, val in required if not val]
        if missing and not self.testing:
            raise ValueError(f"Missing required settings: {', '.join(missing)}")
        return self

    @model_validator(mode="after")
    def validate_optional_features(self):
        if self.enable_tracer and not self.otel_exporter_otlp_endpoint:
            raise ValueError("otel_exporter_otlp_endpoint is required when ENABLE_TRACER=true")
        return self

    model_config = SettingsConfigDict(
        env_file="auth_service/.env.auth",  # Local env file for standalone runs
        env_prefix="",
        case_sensitive=False,
    )


settings = Settings()
