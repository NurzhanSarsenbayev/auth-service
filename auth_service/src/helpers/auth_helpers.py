from http import HTTPStatus

import redis.asyncio as Redis
from core.config import settings
from fastapi import HTTPException, Response
from models import User
from schemas.auth import TokenPair
from sqlalchemy.ext.asyncio import AsyncSession
from utils.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_ttl,
)


# ---------- Token issuing ----------
def issue_tokens(user: User) -> TokenPair:
    """Create access and refresh tokens for a user."""
    payload = {"sub": str(user.user_id), "email": user.email}
    return TokenPair(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload),
        token_type="bearer",
    )


# ---------- Cookies ----------
def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Set refresh token as an HTTP-only cookie."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.testing,
        samesite="strict",
        max_age=30 * 24 * 60 * 60,  # 30 дней
    )


def clear_refresh_cookie(response: Response) -> None:
    """Remove refresh token cookie."""
    response.delete_cookie("refresh_token")


# ---------- Validation ----------
async def validate_refresh(
    refresh_token: str | None,
    session: AsyncSession,
    redis: Redis,
    auth_service,
) -> User:
    if not refresh_token:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="No refresh token provided",
        )

    try:
        payload = await decode_token(refresh_token, redis)
    except HTTPException:
        raise

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await auth_service.repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="User not found",
        )

    return user


# ---------- Blacklist ----------
async def blacklist_token(redis: Redis, token: str) -> None:
    ttl = get_token_ttl(token)
    payload = await decode_token(token, redis)
    jti = payload.get("jti") or token  # запасной ключ
    await redis.setex(f"blacklist:{jti}", ttl, "1")
