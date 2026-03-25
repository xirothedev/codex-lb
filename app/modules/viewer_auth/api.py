from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import JSONResponse

from app.core.auth.dependencies import set_dashboard_error_format
from app.core.exceptions import DashboardAuthError
from app.dependencies import ViewerAuthContext, get_viewer_auth_context
from app.modules.api_keys.service import ApiKeyInvalidError
from app.modules.viewer_auth.schemas import ViewerAuthSessionResponse, ViewerLoginRequest
from app.modules.viewer_auth.service import (
    VIEWER_SESSION_COOKIE,
    VIEWER_SESSION_TTL_SECONDS,
)

router = APIRouter(
    prefix="/api/viewer-auth",
    tags=["viewer"],
    dependencies=[Depends(set_dashboard_error_format)],
)


@router.get("/session", response_model=ViewerAuthSessionResponse)
async def get_viewer_auth_session(
    request: Request,
    context: ViewerAuthContext = Depends(get_viewer_auth_context),
) -> ViewerAuthSessionResponse:
    session_id = request.cookies.get(VIEWER_SESSION_COOKIE)
    return await context.service.get_session_state(session_id)


@router.post("/login", response_model=ViewerAuthSessionResponse)
async def login_viewer(
    request: Request,
    payload: ViewerLoginRequest = Body(...),
    context: ViewerAuthContext = Depends(get_viewer_auth_context),
) -> ViewerAuthSessionResponse | JSONResponse:
    try:
        session_id, response = await context.service.login(payload.api_key)
    except ApiKeyInvalidError as exc:
        raise DashboardAuthError(str(exc), code="invalid_api_key") from exc
    json_response = JSONResponse(status_code=200, content=response.model_dump(mode="json", by_alias=True))
    _set_viewer_session_cookie(json_response, session_id, request)
    return json_response


@router.post("/logout")
async def logout_viewer(
    request: Request,
    context: ViewerAuthContext = Depends(get_viewer_auth_context),
) -> JSONResponse:
    session_id = request.cookies.get(VIEWER_SESSION_COOKIE)
    context.service.logout(session_id)
    response = JSONResponse(status_code=200, content={"status": "ok"})
    response.delete_cookie(key=VIEWER_SESSION_COOKIE, path="/")
    return response


def _set_viewer_session_cookie(response: JSONResponse, session_id: str, request: Request) -> None:
    response.set_cookie(
        key=VIEWER_SESSION_COOKIE,
        value=session_id,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        max_age=VIEWER_SESSION_TTL_SECONDS,
        path="/",
    )
