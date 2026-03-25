from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from app.core.auth.dependencies import set_dashboard_error_format, validate_viewer_session
from app.dependencies import ViewerPortalContext, get_viewer_portal_context
from app.modules.request_logs.schemas import RequestLogFilterOptionsResponse, RequestLogsResponse
from app.modules.request_logs.service import RequestLogModelOption as ServiceRequestLogModelOption
from app.modules.viewer_auth.api import _set_viewer_session_cookie
from app.modules.viewer_auth.schemas import ViewerApiKeyRegenerateResponse, ViewerApiKeyResponse
from app.modules.viewer_auth.service import VIEWER_SESSION_COOKIE, ViewerSessionState, _to_viewer_api_key_response

router = APIRouter(
    prefix="/api/viewer",
    tags=["viewer"],
    dependencies=[Depends(set_dashboard_error_format), Depends(validate_viewer_session)],
)

_MODEL_OPTION_DELIMITER = ":::"


def _parse_model_option(value: str) -> ServiceRequestLogModelOption | None:
    raw = (value or "").strip()
    if not raw:
        return None
    if _MODEL_OPTION_DELIMITER not in raw:
        return ServiceRequestLogModelOption(model=raw, reasoning_effort=None)
    model, effort = raw.split(_MODEL_OPTION_DELIMITER, 1)
    model = model.strip()
    effort = effort.strip()
    if not model:
        return None
    return ServiceRequestLogModelOption(model=model, reasoning_effort=effort or None)


@router.get("/api-key", response_model=ViewerApiKeyResponse)
async def get_viewer_api_key(
    session: ViewerSessionState = Depends(validate_viewer_session),
    context: ViewerPortalContext = Depends(get_viewer_portal_context),
) -> ViewerApiKeyResponse:
    api_key = await context.service.get_api_key(session.api_key_id)
    return _to_viewer_api_key_response(api_key)


@router.post("/api-key/regenerate", response_model=ViewerApiKeyRegenerateResponse)
async def regenerate_viewer_api_key(
    request: Request,
    session: ViewerSessionState = Depends(validate_viewer_session),
    context: ViewerPortalContext = Depends(get_viewer_portal_context),
) -> ViewerApiKeyRegenerateResponse | JSONResponse:
    next_session_id, payload = await context.auth_service.regenerate_authenticated_key(
        request.cookies.get(VIEWER_SESSION_COOKIE)
    )
    json_response = JSONResponse(status_code=200, content=payload.model_dump(mode="json", by_alias=True))
    _set_viewer_session_cookie(json_response, next_session_id, request)
    return json_response


@router.get("/request-logs", response_model=RequestLogsResponse)
async def list_viewer_request_logs(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: str | None = Query(default=None),
    status: list[str] | None = Query(default=None),
    model: list[str] | None = Query(default=None),
    reasoning_effort: list[str] | None = Query(default=None, alias="reasoningEffort"),
    model_option: list[str] | None = Query(default=None, alias="modelOption"),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    session: ViewerSessionState = Depends(validate_viewer_session),
    context: ViewerPortalContext = Depends(get_viewer_portal_context),
) -> RequestLogsResponse:
    parsed_options: list[ServiceRequestLogModelOption] | None = None
    if model_option:
        parsed = [_parse_model_option(value) for value in model_option]
        parsed_options = [value for value in parsed if value is not None] or None
    page = await context.service.list_request_logs(
        api_key_id=session.api_key_id,
        limit=limit,
        offset=offset,
        search=search,
        since=since,
        until=until,
        model_options=parsed_options,
        models=model,
        reasoning_efforts=reasoning_effort,
        status=status,
    )
    scrubbed = [request_log.model_copy(update={"account_id": None, "api_key_name": None}) for request_log in page.requests]
    return RequestLogsResponse(requests=scrubbed, total=page.total, has_more=page.has_more)


@router.get("/request-logs/options", response_model=RequestLogFilterOptionsResponse)
async def list_viewer_request_log_filter_options(
    status: list[str] | None = Query(default=None),
    model: list[str] | None = Query(default=None),
    reasoning_effort: list[str] | None = Query(default=None, alias="reasoningEffort"),
    model_option: list[str] | None = Query(default=None, alias="modelOption"),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    session: ViewerSessionState = Depends(validate_viewer_session),
    context: ViewerPortalContext = Depends(get_viewer_portal_context),
) -> RequestLogFilterOptionsResponse:
    _ = status
    parsed_options: list[ServiceRequestLogModelOption] | None = None
    if model_option:
        parsed = [_parse_model_option(value) for value in model_option]
        parsed_options = [value for value in parsed if value is not None] or None
    options = await context.service.list_request_log_options(
        api_key_id=session.api_key_id,
        since=since,
        until=until,
        model_options=parsed_options,
        models=model,
        reasoning_efforts=reasoning_effort,
    )
    return RequestLogFilterOptionsResponse(
        account_ids=[],
        model_options=[
            {"model": option.model, "reasoning_effort": option.reasoning_effort}
            for option in options.model_options
        ],
        statuses=options.statuses,
    )
