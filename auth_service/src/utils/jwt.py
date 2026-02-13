import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import jwt
from core.config import settings
from fastapi import HTTPException, status
from jwcrypto import jwk
from redis.asyncio import Redis

# ---------- Constants ----------
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


# ---------- Signing / Generation ----------
def create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + expires_delta
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "type": token_type, "jti": jti})
    key = jwk.JWK.from_pem(settings.jwt_private_key.encode())
    header = {"alg": settings.jwt_algorithm, "kid": key.thumbprint()}
    return jwt.encode(
        to_encode,
        settings.jwt_private_key,
        algorithm=settings.jwt_algorithm,
        headers=header,
    )


def create_access_token(data: dict) -> str:
    return create_token(data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "access")


def create_refresh_token(data: dict) -> str:
    return create_token(data, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), "refresh")


def create_token_pair(user_id: str, email: str) -> dict[str, str]:
    payload = {"sub": user_id, "email": email}
    return {
        "access_token": create_access_token(payload),
        "refresh_token": create_refresh_token(payload),
        "token_type": "bearer",
    }


# ---------- Blacklist ----------
async def is_token_blacklisted(redis: Redis | None, jti: str) -> bool:
    if not redis:
        return False
    exists = await redis.exists(f"blacklist:{jti}")
    return cast(int, exists) > 0


# ---------- Decode + Verification ----------
async def decode_token(token: str, redis: Redis | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_public_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from None

    # Blacklist check
    jti = payload.get("jti")
    if jti and await is_token_blacklisted(redis, jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    return payload


# ---------- TTL ----------
def get_token_ttl(token: str) -> int:
    """Return token TTL in seconds (for Redis)."""
    payload = jwt.decode(
        token,
        settings.jwt_public_key,
        algorithms=[settings.jwt_algorithm],
        options={"verify_exp": False},
    )
    exp = payload.get("exp")
    if not exp:
        return 0
    now = datetime.now(UTC).timestamp()
    return max(0, int(exp - now))
