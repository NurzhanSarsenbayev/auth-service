import pytest
from httpx import AsyncClient
from http import HTTPStatus


@pytest.mark.asyncio
async def test_login_oauth2_success(client: AsyncClient, create_user):
    await create_user("john", "john@example.com", "password123")

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "john", "password": "password123"},
    )
    tokens = response.json()
    assert "access_token" in tokens
    assert "token_type" in tokens
    assert "refresh_token" not in tokens
    assert response.cookies.get("refresh_token") is not None

@pytest.mark.asyncio
async def test_login_oauth2_invalid_credentials(
        client: AsyncClient, create_user):
    await create_user("mike", "mike@example.com", "password123")

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "mike", "password": "wrongpass"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_login_json_success(client: AsyncClient, create_user):
    await create_user("alice", "alice@example.com", "password123")

    response = await client.post(
        "/api/v1/auth/login-json",
        json={"username": "alice", "password": "password123"},
    )
    tokens = response.json()
    assert "access_token" in tokens
    assert "token_type" in tokens
    assert "refresh_token" not in tokens
    assert response.cookies.get("refresh_token") is not None

@pytest.mark.asyncio
async def test_login_json_invalid_credentials(
        client: AsyncClient, create_user):
    await create_user("bob", "bob@example.com", "password123")

    response = await client.post(
        "/api/v1/auth/login-json",
        json={"username": "bob", "password": "wrongpass"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient, create_user):
    await create_user("kate", "kate@example.com", "password123")

    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "kate", "password": "password123"},
    )
    old_refresh = login_resp.cookies.get("refresh_token")
    assert old_refresh is not None

    # Call refresh with the cookie
    client.cookies.set("refresh_token", old_refresh)
    refresh_resp = await client.post("/api/v1/auth/refresh")

    assert refresh_resp.status_code == HTTPStatus.OK

    # Rotation MUST set a new cookie
    new_refresh = refresh_resp.cookies.get("refresh_token")
    assert new_refresh is not None
    assert new_refresh != old_refresh

    # Optional but useful: ensure Set-Cookie header exists
    assert "set-cookie" in refresh_resp.headers

    tokens = refresh_resp.json()
    assert "access_token" in tokens
    assert "token_type" in tokens
    assert "refresh_token" not in tokens

    new_refresh_cookie = refresh_resp.cookies.get("refresh_token")
    assert new_refresh_cookie is not None

@pytest.mark.asyncio
async def test_refresh_old_cookie_rejected_after_rotation(
    client: AsyncClient, create_user
):
    await create_user("lisa", "lisa@example.com", "password123")

    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "lisa", "password": "password123"},
    )
    old_refresh = login_resp.cookies.get("refresh_token")
    assert old_refresh is not None

    # First refresh -> rotates cookie
    client.cookies.set("refresh_token", old_refresh)
    first_refresh = await client.post("/api/v1/auth/refresh")
    assert first_refresh.status_code == HTTPStatus.OK

    new_refresh = first_refresh.cookies.get("refresh_token")
    assert new_refresh is not None
    assert new_refresh != old_refresh

    # Now try to refresh AGAIN with the OLD cookie -> must be rejected
    client.cookies.set("refresh_token", old_refresh)
    second_refresh = await client.post("/api/v1/auth/refresh")
    assert second_refresh.status_code == HTTPStatus.UNAUTHORIZED

@pytest.mark.asyncio
async def test_refresh_no_cookie(client: AsyncClient):
    client.cookies.clear()
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_logout_blacklist(
        client: AsyncClient, create_user, redis_client):
    await create_user("nick", "nick@example.com", "password123")

    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "nick", "password": "password123"},
    )
    assert login_resp.status_code == HTTPStatus.OK

    refresh_cookie = login_resp.cookies.get("refresh_token")
    assert refresh_cookie is not None

    logout_resp = await client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == HTTPStatus.OK
    assert logout_resp.json()["detail"] == "Logged out successfully"

    keys = await redis_client.keys("blacklist:*")
    assert len(keys) > 0

    assert client.cookies.get("refresh_token") is None
