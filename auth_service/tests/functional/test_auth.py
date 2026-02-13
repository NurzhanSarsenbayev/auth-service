import pytest
from httpx import AsyncClient
from http import HTTPStatus


@pytest.mark.asyncio
async def test_login_oauth2_success(client: AsyncClient, create_user):
    """Успешный логин через /login (form-data)"""
    await create_user("john", "john@example.com", "password123")

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "john", "password": "password123"},
    )
    assert response.status_code == HTTPStatus.OK
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert response.cookies.get("refresh_token") is not None


@pytest.mark.asyncio
async def test_login_oauth2_invalid_credentials(
        client: AsyncClient, create_user):
    """Ошибка при неверном пароле через /login"""
    await create_user("mike", "mike@example.com", "password123")

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "mike", "password": "wrongpass"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_login_json_success(client: AsyncClient, create_user):
    """Успешный логин через /login-json (JSON body)"""
    await create_user("alice", "alice@example.com", "password123")

    response = await client.post(
        "/api/v1/auth/login-json",
        json={"username": "alice", "password": "password123"},
    )
    assert response.status_code == HTTPStatus.OK
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    # ❌ куку тут не проверяем, т.к. это чистый REST endpoint


@pytest.mark.asyncio
async def test_login_json_invalid_credentials(
        client: AsyncClient, create_user):
    """Ошибка при неверном пароле через /login-json"""
    await create_user("bob", "bob@example.com", "password123")

    response = await client.post(
        "/api/v1/auth/login-json",
        json={"username": "bob", "password": "wrongpass"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient, create_user):
    """Успешное обновление токенов через /refresh (cookie refresh_token)"""
    await create_user("kate", "kate@example.com", "password123")

    # логинимся через /login → получаем cookie
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "kate", "password": "password123"},
    )
    refresh_cookie = login_resp.cookies.get("refresh_token")
    assert refresh_cookie is not None

    # обновляем токены
    client.cookies.set("refresh_token", refresh_cookie)
    refresh_resp = await client.post("/api/v1/auth/refresh")

    assert refresh_resp.status_code == HTTPStatus.OK
    tokens = refresh_resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens


@pytest.mark.asyncio
async def test_refresh_no_cookie(client: AsyncClient):
    """Ошибка при отсутствии cookie в /refresh"""
    client.cookies.clear()   # 👈 сбрасываем куки
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_logout_blacklist(
        client: AsyncClient, create_user, redis_client):
    """Logout добавляет refresh_token в blacklist и очищает cookie"""
    await create_user("nick", "nick@example.com", "password123")

    # логинимся через /login → кука ставится автоматически
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "nick", "password": "password123"},
    )
    assert login_resp.status_code == HTTPStatus.OK

    refresh_cookie = login_resp.cookies.get("refresh_token")
    assert refresh_cookie is not None

    # вызываем logout
    logout_resp = await client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == HTTPStatus.OK
    assert logout_resp.json()["detail"] == "Logged out successfully"

    # проверяем что токен попал в blacklist
    keys = await redis_client.keys("blacklist:*")
    assert len(keys) > 0

    # проверяем что кука очищена
    assert client.cookies.get("refresh_token") is None
