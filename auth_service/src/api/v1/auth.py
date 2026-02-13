from http import HTTPStatus

from core.config import settings
from fastapi import APIRouter, Cookie, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from jwcrypto import jwk
from schemas.auth import LoginRequest, TokenPair
from services.auth import AuthService
from utils.dependencies import get_auth_service

router = APIRouter()


@router.post("/login", response_model=TokenPair, status_code=HTTPStatus.OK)
async def login_oauth2(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.login_with_form(
        form_data.username, form_data.password, request, response
    )


@router.post("/login-json", response_model=TokenPair, status_code=HTTPStatus.OK)
async def login_json(
    data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.login_with_json(data.username, data.password)


@router.post("/refresh", response_model=TokenPair, status_code=HTTPStatus.OK)
async def refresh_tokens(
    refresh_token: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.refresh_by_cookie(refresh_token)


@router.post("/logout", status_code=HTTPStatus.OK)
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    refresh_token = request.cookies.get("refresh_token")
    return await auth_service.logout_by_cookie(refresh_token, response)


@router.get("/.well-known/jwks.json")
async def jwks():
    key = jwk.JWK.from_pem(settings.jwt_public_key.encode())
    return {"keys": [key.export(private_key=False, as_dict=True)]}
