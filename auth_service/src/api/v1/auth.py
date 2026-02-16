from http import HTTPStatus

from fastapi import APIRouter, Cookie, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from helpers.auth_helpers import set_refresh_cookie
from schemas.auth import AccessTokenResponse, LoginRequest
from services.auth import AuthService
from utils.dependencies import get_auth_service

router = APIRouter()


@router.post("/login", response_model=AccessTokenResponse, status_code=HTTPStatus.OK)
async def login_oauth2(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    tokens = await auth_service.login_with_form(
        form_data.username, form_data.password, request, response
    )
    return {"access_token": tokens.access_token, "token_type": tokens.token_type}


@router.post("/login-json", response_model=AccessTokenResponse, status_code=HTTPStatus.OK)
async def login_json(
    data: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    tokens = await auth_service.login_with_json(data.username, data.password)
    set_refresh_cookie(response, tokens.refresh_token)
    return {"access_token": tokens.access_token, "token_type": tokens.token_type}


@router.post("/refresh", response_model=AccessTokenResponse, status_code=HTTPStatus.OK)
async def refresh_tokens(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
):
    tokens = await auth_service.refresh_by_cookie(refresh_token)
    set_refresh_cookie(response, tokens.refresh_token)
    return {"access_token": tokens.access_token, "token_type": tokens.token_type}


@router.post("/logout", status_code=HTTPStatus.OK)
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    refresh_token = request.cookies.get("refresh_token")
    return await auth_service.logout_by_cookie(refresh_token, response)
