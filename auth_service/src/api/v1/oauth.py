from http import HTTPStatus

from db.postgres import get_session
from fastapi import APIRouter, Depends, HTTPException, Query
from models import User
from services.oauth import OAuthService
from services.user import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse
from utils.dependencies import get_current_user, get_oauth_service, get_user_service

router = APIRouter()


@router.get("/{provider}/login", status_code=HTTPStatus.TEMPORARY_REDIRECT)
async def oauth_login(
    provider: str,
    service: OAuthService = Depends(get_oauth_service),
):
    """Redirect the user to the selected OAuth provider authorization page."""
    url = service.get_authorize_url(provider)
    return RedirectResponse(url=url, status_code=HTTPStatus.TEMPORARY_REDIRECT)


@router.get("/{provider}/callback", status_code=HTTPStatus.OK)
async def oauth_callback(
    provider: str,
    code: str | None = Query(default=None),
    error: str | None = Query(default=None),
    state: str | None = Query(default=None),
    db: AsyncSession = Depends(get_session),
    service: OAuthService = Depends(get_oauth_service),
    user_service: UserService = Depends(get_user_service),
):
    if error:
        raise HTTPException(HTTPStatus.BAD_REQUEST, f"OAuth error from {provider}: {error}")
    if not code:
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Missing 'code' in OAuth callback")

    return await service.handle_callback(provider, code, db, user_service)


@router.delete("/{provider}/unlink", status_code=HTTPStatus.NO_CONTENT)
async def unlink_social_account(
    provider: str,
    db: AsyncSession = Depends(get_session),
    service: OAuthService = Depends(get_oauth_service),
    current_user: User = Depends(get_current_user),
):
    await service.unlink(provider=provider, user_id=current_user.user_id, db=db)
