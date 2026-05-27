from __future__ import annotations

from pydantic import BaseModel, Field


class ViewerLoginRequest(BaseModel):
    api_key: str = Field(min_length=1)


class ViewerLoginResponse(BaseModel):
    token: str
    expires_in: int


class ViewerSessionData(BaseModel):
    api_key_id: str
