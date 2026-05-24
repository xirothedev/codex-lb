from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from app.core.auth.dependencies import _validate_api_key_token
from app.core.exceptions import ProxyAuthError
from app.modules.api_keys.service import ApiKeyInvalidError, ApiKeysService
from app.modules.viewer_auth.schemas import ViewerLoginRequest, ViewerLoginResponse, ViewerSessionData
from app.modules.viewer_auth.service import get_viewer_session_store
from app.db.session import get_background_session

router = APIRouter(prefix="/viewer/auth", tags=["viewer-auth"])

_SESSION_COOKIE = "viewer_session"


@router.post("/login", response_model=ViewerLoginResponse)
async def login(request: ViewerLoginRequest, response: Response):
    try:
        async with get_background_session() as session:
            from app.modules.api_keys.repository import ApiKeysRepository

            service = ApiKeysService(ApiKeysRepository(session))
            key_data = await service.validate_key(request.api_key)
    except ApiKeyInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    if not key_data.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key is inactive")

    session_data = ViewerSessionData(
        api_key_id=key_data.key_id,
        key_name=key_data.name,
        is_active=key_data.is_active,
    )
    store = get_viewer_session_store()
    token, expires_in = store.create(session_data)

    response.set_cookie(
        key=_SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="strict",
        max_age=expires_in,
        path="/viewer",
    )
    return ViewerLoginResponse(token=token, expires_in=expires_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    viewer_session: str | None = Cookie(None, alias=_SESSION_COOKIE),
):
    if viewer_session:
        get_viewer_session_store().delete(viewer_session)
    response.delete_cookie(key=_SESSION_COOKIE, path="/viewer")
