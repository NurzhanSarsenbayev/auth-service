import pytest
from httpx import AsyncClient
from uuid import uuid4
from http import HTTPStatus


@pytest.mark.asyncio
async def test_assign_and_check_role(client: AsyncClient):
    """Назначение роли пользователю и проверка её наличия"""
    # создаём юзера
    user_resp = await client.post(
        "/api/v1/users/signup",
        json={
            "username": "roleuser",
            "email": "roleuser@example.com",
            "password": "pass123"
        },
    )
    user_id = user_resp.json()["user_id"]

    # логинимся админом
    login_resp = await client.post(
        "/api/v1/auth/login-json",
        json={
            "username": "admin",
            "password": "123"
        }
    )
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # создаём роль
    role_name = f"user_{uuid4().hex[:6]}"
    role_resp = await client.post(
        "/api/v1/roles/create",
        json={"name": role_name, "description": "Test role"},
        headers=headers,
    )
    role_id = role_resp.json()["role_id"]

    # назначаем роль
    assign_resp = await client.post(
        "/api/v1/user_roles/assign",
        json={"user_id": user_id, "role_id": role_id},
        headers=headers,
    )
    assert assign_resp.status_code == HTTPStatus.CREATED

    # проверяем роль
    check_resp = await client.post(
        "/api/v1/user_roles/check",
        json={"user_id": user_id, "role_name": role_name},
        headers=headers,
    )
    assert check_resp.status_code == HTTPStatus.OK
    assert check_resp.json()["allowed"] is True


@pytest.mark.asyncio
async def test_remove_role_from_user(client: AsyncClient):
    """Удаление роли у пользователя"""
    # создаём юзера
    user_resp = await client.post(
        "/api/v1/users/signup",
        json={
            "username": "removeuser",
            "email": "remove@example.com",
            "password": "pass123"
        },
    )
    user_id = user_resp.json()["user_id"]

    # логинимся админом
    login_resp = await client.post(
        "/api/v1/auth/login-json",
        json={
            "username": "admin",
            "password": "123"
        }
    )
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # создаём роль
    role_name = f"removerole_{uuid4().hex[:6]}"
    role_resp = await client.post(
        "/api/v1/roles/create",
        json={
            "name": role_name,
            "description": "Role for remove test"
        },
        headers=headers,
    )
    role_id = role_resp.json()["role_id"]

    # назначаем роль
    await client.post(
        "/api/v1/user_roles/assign",
        json={"user_id": user_id, "role_id": role_id},
        headers=headers,
    )

    # удаляем роль
    delete_resp = await client.delete(
        f"/api/v1/user_roles/{user_id}/roles/{role_id}", headers=headers
    )
    assert delete_resp.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.asyncio
async def test_current_user(client: AsyncClient):
    """Эндпоинт /me возвращает текущего пользователя"""
    # логинимся админом
    login_resp = await client.post(
        "/api/v1/auth/login-json",
        json={
            "username": "admin",
            "password": "123"
        }
    )
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    me_resp = await client.get("/api/v1/user_roles/me", headers=headers)
    assert me_resp.status_code == HTTPStatus.OK
    data = me_resp.json()
    assert data["username"] == "admin"


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient):
    """Список пользователей с их ролями"""
    # логинимся админом
    login_resp = await client.post(
        "/api/v1/auth/login-json",
        json={
            "username": "admin",
            "password": "123"
        }
    )
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get("/api/v1/user_roles/list", headers=headers)
    assert resp.status_code == HTTPStatus.OK
    assert isinstance(resp.json(), list)
