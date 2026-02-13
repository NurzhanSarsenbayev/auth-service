import json

from core.config import settings
from fastapi import APIRouter
from jwcrypto import jwk

router = APIRouter()


@router.get("/.well-known/jwks.json")
async def jwks():
    key = jwk.JWK.from_pem(settings.jwt_public_key.encode())
    kid = key.thumbprint()
    pub = json.loads(key.export(private_key=False))
    pub["kid"] = kid
    pub["alg"] = "RS256"
    pub["use"] = "sig"
    return {"keys": [pub]}
