from typing import TypedDict

from models import User
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    username: str  # OAuth2 username
    email: EmailStr  # optional, if you want to store email
    password: str


class AuthResult(TypedDict):
    user: User
    tokens: TokenPair
