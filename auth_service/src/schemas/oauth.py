from pydantic import BaseModel


class OAuthCallbackResponse(BaseModel):
    user_id: str
    email: str
    access_token: str
    refresh_token: str
    provider: str
