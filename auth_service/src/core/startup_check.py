from __future__ import annotations

import os

from core.config import settings


def validate_runtime_environment() -> None:
    missing: list[str] = []

    if not os.path.exists(settings.jwt_private_key_path):
        missing.append(f"JWT private key not found: {settings.jwt_private_key_path}")

    if not os.path.exists(settings.jwt_public_key_path):
        missing.append(f"JWT public key not found: {settings.jwt_public_key_path}")

    if missing:
        hint = "Generate keys as described in auth_service/keys/README.md"
        raise RuntimeError("\n".join([*missing, hint]))
