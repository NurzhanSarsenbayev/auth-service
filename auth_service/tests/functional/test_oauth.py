import json
import pytest
from http import HTTPStatus
from httpx import AsyncClient
from jwt import decode as jwt_decode, get_unverified_header
from jwt.algorithms import RSAAlgorithm


@pytest.mark.asyncio
async def test_jwks_shape(client: AsyncClient):
    resp = await client.get("/.well-known/jwks.json")
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert isinstance(data.get("keys"), list) and len(data["keys"]) >= 1

    jwk = data["keys"][0]
    for field in ("kty", "n", "e", "kid"):
        assert field in jwk
    assert jwk["kty"] == "RSA"


@pytest.mark.asyncio
async def test_jwks_verifies_our_token(client: AsyncClient, create_user):
    await create_user("jwksuser", "jwks@example.com", "secret123")
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "jwksuser", "password": "secret123"},
    )
    assert login_resp.status_code == HTTPStatus.OK
    token = login_resp.json()["access_token"]

    jwks_resp = await client.get("/.well-known/jwks.json")
    assert jwks_resp.status_code == HTTPStatus.OK
    jwks = jwks_resp.json()["keys"]

    kid = get_unverified_header(token)["kid"]
    key_dict = next(k for k in jwks if k["kid"] == kid)

    public_key = RSAAlgorithm.from_jwk(json.dumps(key_dict))
    claims = jwt_decode(
        token,
        key=public_key,
        algorithms=["RS256"],
        options={"verify_aud": False},
    )
    assert claims.get("sub")


@pytest.mark.asyncio
async def test_oauth_login_redirect(client: AsyncClient):
    resp = await client.get("/api/v1/oauth/google/login",
                            follow_redirects=False)
    assert resp.status_code == HTTPStatus.TEMPORARY_REDIRECT
    location = resp.headers.get("Location")
    assert location and "google" in location.lower()
