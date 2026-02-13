import pytest
from httpx import AsyncClient
from http import HTTPStatus


@pytest.mark.asyncio
async def test_create_role(client: AsyncClient):
    login_resp = await client.post(
        "/api/v1/auth/login-json",
        json={"username": "admin", "password": "123"},
    )
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.post(
        "/api/v1/roles/create",
        json={"name": "editor", "description": "Can edit content"},
        headers=headers,
    )
    assert resp.status_code == HTTPStatus.CREATED
    data = resp.json()
    assert data["name"] == "editor"
    assert data["description"] == "Can edit content"


@pytest.mark.asyncio
async def test_list_roles(client: AsyncClient):
    login_resp = await client.post(
        "/api/v1/auth/login-json",
        json={"username": "admin", "password": "123"},
    )
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    await client.post(
        "/api/v1/roles/create",
        json={"name": "viewer", "description": "Can view content"},
        headers=headers,
    )

    resp = await client.get("/api/v1/roles/list", headers=headers)
    assert resp.status_code == HTTPStatus.OK
    roles = resp.json()
    assert any(r["name"] == "viewer" for r in roles)


@pytest.mark.asyncio
async def test_update_role(client: AsyncClient):
    login_resp = await client.post(
        "/api/v1/auth/login-json",
        json={"username": "admin", "password": "123"},
    )
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    create_resp = await client.post(
        "/api/v1/roles/create",
        json={"name": "tester", "description": "Can test system"},
        headers=headers,
    )
    role_id = create_resp.json()["role_id"]

    update_resp = await client.put(
        f"/api/v1/roles/update/{role_id}",
        json={"description": "Can test and report bugs"},
        headers=headers,
    )
    assert update_resp.status_code == HTTPStatus.OK
    updated = update_resp.json()
    assert updated["description"] == "Can test and report bugs"


@pytest.mark.asyncio
async def test_delete_role(client: AsyncClient):
    login_resp = await client.post(
        "/api/v1/auth/login-json",
        json={"username": "admin", "password": "123"},
    )
    tokens = login_resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    create_resp = await client.post(
        "/api/v1/roles/create",
        json={"name": "deleteme", "description": "To be deleted"},
        headers=headers,
    )
    role_id = create_resp.json()["role_id"]

    delete_resp = await client.delete(
        f"/api/v1/roles/delete/{role_id}", headers=headers)
    assert delete_resp.status_code == HTTPStatus.NO_CONTENT

    list_resp = await client.get("/api/v1/roles/list", headers=headers)
    assert list_resp.status_code == HTTPStatus.OK
    roles = list_resp.json()
    assert all(r["role_id"] != role_id for r in roles)
