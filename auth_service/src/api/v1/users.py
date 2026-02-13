from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, Params
from models import User
from schemas.user import (
    LoginHistoryItem,
    UserCreate,
    UserRead,
    UserUpdateRequest,
    UserUpdateResponse,
)
from services.user import UserService
from utils.dependencies import get_current_user, get_current_user_with_roles, get_user_service

router = APIRouter()


@router.post("/signup", response_model=UserRead, status_code=HTTPStatus.CREATED)
async def register_user(user_data: UserCreate, service: UserService = Depends(get_user_service)):
    return await service.create_user(user_data.username, user_data.email, user_data.password)


@router.get("/user/history", response_model=Page[LoginHistoryItem], status_code=HTTPStatus.OK)
async def get_login_history(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
    params: Params = Depends(),
):
    return await service.get_login_history(current_user.user_id, params)


@router.patch("/auth/update", response_model=UserUpdateResponse, status_code=HTTPStatus.OK)
async def update_user(
    update: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return await service.update_user(current_user, update)


@router.delete("/{user_id}", status_code=HTTPStatus.NO_CONTENT)
async def delete_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
    _: None = Depends(get_current_user_with_roles(["admin"])),
):
    return await service.delete_user(user_id)
