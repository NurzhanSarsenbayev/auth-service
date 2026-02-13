import pytest
from httpx import AsyncClient
from http import HTTPStatus


@pytest.mark.asyncio
async def test_signup_success(client: AsyncClient):
    """Регистрация нового пользователя"""
    resp = await client.post(
        "/api/v1/users/signup",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "pass123"
        },
    )
    assert resp.status_code == HTTPStatus.CREATED
    data = resp.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"


@pytest.mark.asyncio
async def test_signup_duplicate_email(client: AsyncClient):
    """Попытка зарегистрировать с уже существующим email"""
    # первый пользователь
    await client.post(
        "/api/v1/users/signup",
        json={
            "username": "u1",
            "email": "dup@example.com",
            "password": "pass123"
        },
    )
    # второй с тем же email
    resp = await client.post(
        "/api/v1/users/signup",
        json={
            "username": "u2",
            "email": "dup@example.com",
            "password": "pass123"
        },
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_get_login_history(client: AsyncClient):
    """Получение истории логинов"""
    # регаем и логинимся
    await client.post(
        "/api/v1/users/signup",
        json={
            "username": "historyuser",
            "email": "history@example.com",
            "password": "pass123"
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login-json",
        json={
            "username": "historyuser",
            "password": "pass123"
        },
    )
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get("/api/v1/users/user/history", headers=headers)
    assert resp.status_code == HTTPStatus.OK
    body = resp.json()
    assert "items" in body
    assert isinstance(body["items"], list)


@pytest.mark.asyncio
async def test_update_username(client: AsyncClient):
    """Обновление username"""
    # регаем юзера
    await client.post(
        "/api/v1/users/signup",
        json={
            "username": "upuser",
            "email": "upuser@example.com",
            "password": "pass123"
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login-json",
        json={
            "username": "upuser",
            "password": "pass123"
        },
    )
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # меняем username
    resp = await client.patch(
        "/api/v1/users/auth/update",
        json={
            "username": "newname"
        },
        headers=headers,
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["message"] == "User data updated successfully"


@pytest.mark.asyncio
async def test_update_password_wrong_old(client: AsyncClient):
    """Обновление пароля с неверным старым"""
    await client.post(
        "/api/v1/users/signup",
        json={
            "username": "pwuser",
            "email": "pwuser@example.com",
            "password": "pass123"
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login-json",
        json={
            "username": "pwuser",
            "password": "pass123"
        },
    )
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.patch(
        "/api/v1/users/auth/update",
        json={
            "old_password": "wrongpass",
            "new_password": "newpass"
        },
        headers=headers,
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.json()["detail"] == "Wrong password"


@pytest.mark.asyncio
async def test_delete_user_as_admin(client: AsyncClient):
    """Удаление пользователя админом"""
    # регаем обычного юзера
    user_resp = await client.post(
        "/api/v1/users/signup",
        json={
            "username": "todelete",
            "email": "todelete@example.com",
            "password": "pass123"
        },
    )
    user_id = user_resp.json()["user_id"]

    # логинимся суперюзером
    login_resp = await client.post(
        "/api/v1/auth/login-json",
        json={
            "username": "admin",
            "password": "123"
        },
    )
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # удаляем
    resp = await client.delete(f"/api/v1/users/{user_id}", headers=headers)
    assert resp.status_code == HTTPStatus.NO_CONTENT

    # проверяем, что юзер исчез
    resp2 = await client.delete(f"/api/v1/users/{user_id}", headers=headers)
    assert resp2.status_code == HTTPStatus.NOT_FOUND
