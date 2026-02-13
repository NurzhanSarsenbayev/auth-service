from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends
from schemas.role import RoleCreate, RoleRead, RoleUpdate
from services.role import RoleService
from utils.dependencies import get_current_user_with_roles, get_role_service

router = APIRouter()


@router.post("/create", response_model=RoleRead, status_code=HTTPStatus.CREATED)
async def create_role(
    data: RoleCreate,
    service: RoleService = Depends(get_role_service),
    _: None = Depends(get_current_user_with_roles(["admin"])),
):
    return await service.create(data)


@router.get("/list", response_model=list[RoleRead], status_code=HTTPStatus.OK)
async def list_roles(service: RoleService = Depends(get_role_service)):
    return await service.list()


@router.put("/update/{role_id}", response_model=RoleRead, status_code=HTTPStatus.OK)
async def update_role(
    role_id: UUID,
    data: RoleUpdate,
    service: RoleService = Depends(get_role_service),
    _: None = Depends(get_current_user_with_roles(["admin"])),
):
    return await service.update(role_id, data)


@router.delete("/delete/{role_id}", status_code=HTTPStatus.NO_CONTENT)
async def delete_role(
    role_id: UUID,
    service: RoleService = Depends(get_role_service),
    _: None = Depends(get_current_user_with_roles(["admin"])),
):
    await service.delete(role_id)
