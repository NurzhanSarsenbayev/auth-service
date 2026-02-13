import redis.asyncio as redis
from core.oauth.providers.google import GoogleOAuthProvider
from core.oauth.providers.yandex import YandexOAuthProvider
from db.postgres import get_session
from db.redis_db import get_redis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from models import Role, User
from repositories.role import RoleRepository
from repositories.user import UserRepository
from repositories.user_role import UserRoleRepository
from schemas.role import RoleResponse
from schemas.user import CurrentUserResponse
from services.auth import AuthService
from services.oauth import OAuthService
from services.role import RoleService
from services.user import UserService
from services.user_role import UserRoleService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.jwt import decode_token

# =============================
# OAuth2 Schemes
# =============================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# =============================
# Internal helper
# =============================
async def _get_user_from_token(
    token: str | None,
    session: AsyncSession,
    redis: redis.Redis,
) -> User | None:
    """Возвращает ORM User из токена. Если токен битый/отсутствует → None."""
    if not token:
        return None

    try:
        payload = await decode_token(token, redis=redis)
    except Exception:
        return None

    if payload.get("type") != "access":
        return None

    result = await session.execute(select(User).where(User.user_id == payload.get("sub")))
    return result.scalar_one_or_none()


# =============================
# Repo providers
# =============================
async def get_user_repo(session: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


async def get_role_repo(session: AsyncSession = Depends(get_session)) -> RoleRepository:
    return RoleRepository(session)


# =============================
# Service providers
# =============================
async def get_auth_service(
    session: AsyncSession = Depends(get_session),
    redis: redis.Redis = Depends(get_redis),
) -> AuthService:
    return AuthService(UserRepository(session), redis)


async def get_role_service(
    session: AsyncSession = Depends(get_session),
    redis: redis.Redis = Depends(get_redis),
) -> RoleService:
    return RoleService(RoleRepository(session), redis)


async def get_user_service(
    session: AsyncSession = Depends(get_session),
    redis: redis.Redis = Depends(get_redis),
) -> UserService:
    return UserService(UserRepository(session), redis)


def get_user_role_service(
    session: AsyncSession = Depends(get_session),
    redis: redis.Redis = Depends(get_redis),
) -> UserRoleService:
    return UserRoleService(UserRoleRepository(session), redis)


# =============================
# Auth dependencies
# =============================
async def _build_guest_principal(session: AsyncSession) -> CurrentUserResponse:
    """Вернёт текущего пользователя-гостя (если нет валидного токена)."""
    # Пытаемся найти роль 'guest' (через репозиторий или прямым запросом)
    try:
        role_repo = RoleRepository(session)
        guest_role = await role_repo.get_by_name("guest")  # если метод есть
    except Exception:
        guest_role = None

    if guest_role is None:
        # надёжный fallback: прямой select
        res = await session.execute(select(Role).where(Role.name == "guest"))
        guest_role = res.scalar_one_or_none()

    roles = [RoleResponse.from_orm(guest_role)] if guest_role else []
    return CurrentUserResponse(id=None, username="guest", email=None, roles=roles)


async def get_current_principal(
    session: AsyncSession = Depends(get_session),
    redis_cli: redis.Redis = Depends(get_redis),
    token: str | None = Depends(oauth2_scheme_optional),
) -> CurrentUserResponse:
    """
    Возвращает:
      - CurrentUserResponse
      для реального пользователя при валидном access-токене
      - CurrentUserResponse
      гостя, если токена нет / он невалиден / не access
    """
    if not token:
        return await _build_guest_principal(session)

    try:
        payload = await decode_token(token, redis=redis_cli)
    except Exception:
        return await _build_guest_principal(session)

    if payload.get("type") != "access":
        return await _build_guest_principal(session)

    user_id = payload.get("sub")
    user_repo = UserRepository(session)
    ur_repo = UserRoleRepository(session)

    user = await user_repo.get_by_id(user_id)
    if not user:
        return await _build_guest_principal(session)

    roles = await ur_repo.get_roles_for_user(user.user_id)
    return CurrentUserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        roles=[RoleResponse.from_orm(r) for r in roles],
    )


# Оставляем строгую зависимость
# для тех маршрутов, где нужен именно ORM-пользователь:


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    redis: redis.Redis = Depends(get_redis),
    token: str = Depends(oauth2_scheme),
) -> User:
    try:
        payload = await decode_token(token, redis=redis)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication") from None

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid authentication") from None

    user_id = payload.get("sub")
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return user


def get_current_user_with_roles(required_roles: list[str]):
    """Декоратор-зависимость: проверка ролей."""

    async def dependency(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_session),
        redis: redis.Redis = Depends(get_redis),
    ) -> User:
        user = await _get_user_from_token(token, session, redis)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        service = UserRoleService(UserRoleRepository(session), redis)
        user_roles = await service.get_user_roles(user.user_id)

        role_names = [r.name for r in user_roles]
        if not any(req in role_names for req in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_roles}, found: {role_names}",
            )

        return user

    return dependency


def get_oauth_service(db: AsyncSession = Depends(get_session)) -> OAuthService:
    providers = {
        "yandex": YandexOAuthProvider(),
        "google": GoogleOAuthProvider(),
    }
    # БД отдаём отдельно через Depends (используем в handle_callback)
    svc = OAuthService(providers=providers)
    # вернём кортеж, чтобы в хэндлере было и svc, и db
    svc.db = db  # простая "инъекция" сеанса
    return svc
