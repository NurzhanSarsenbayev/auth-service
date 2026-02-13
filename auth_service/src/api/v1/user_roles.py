from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends
from schemas.role import RoleAssignRequest, RoleCheckRequest, RoleCheckResponse
from schemas.user import CurrentUserResponse
from schemas.user_role import UserRoleListResponse
from services.user_role import UserRoleService
from utils.dependencies import get_current_principal, get_user_role_service

router = APIRouter()


@router.post("/assign", status_code=HTTPStatus.CREATED)
async def assign_role(
    req: RoleAssignRequest, service: UserRoleService = Depends(get_user_role_service)
):
    return await service.assign_role_to_user(req.user_id, req.role_id)


@router.delete("/{user_id}/roles/{role_id}", status_code=HTTPStatus.NO_CONTENT)
async def remove_role_from_user(
    user_id: UUID, role_id: UUID, service: UserRoleService = Depends(get_user_role_service)
):
    return await service.remove_role_from_user(user_id, role_id)


@router.post("/check", response_model=RoleCheckResponse)
async def check_role(
    req: RoleCheckRequest, service: UserRoleService = Depends(get_user_role_service)
):
    return await service.check_role(req.user_id, req.role_name)


@router.get("/me", response_model=CurrentUserResponse)
async def current_user_me(
    principal: CurrentUserResponse = Depends(get_current_principal),
    service: UserRoleService = Depends(get_user_role_service),
):
    return await service.current_user_info(principal)


@router.get("/list", response_model=list[UserRoleListResponse])
async def list_users(service: UserRoleService = Depends(get_user_role_service)):
    return await service.list_all_users()
