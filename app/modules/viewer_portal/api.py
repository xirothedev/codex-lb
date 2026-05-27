from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import ApiKeysContext, get_api_keys_context
from app.db.session import get_session
from app.modules.api_keys.schemas import (
    ApiKeyAccountCostResponse,
    ApiKeyTrendPoint,
    ApiKeyTrendsResponse,
    ApiKeyUsage7DayResponse,
)
from app.modules.api_keys.service import ApiKeyData, ApiKeyInvalidError
from app.modules.viewer_auth.schemas import ViewerSessionData
from app.modules.viewer_auth.service import get_viewer_session_store
from app.modules.viewer_portal.schemas import (
    ViewerKeyInfo,
    ViewerQuotaEntry,
    ViewerRequestLogsResponse,
    ViewerUsageSummary,
)
from app.modules.viewer_portal.service import ViewerPortalService

router = APIRouter(prefix="/viewer", tags=["viewer-portal"])

_SESSION_COOKIE = "viewer_session"


async def _get_viewer_session(
    viewer_session: str | None = Cookie(None, alias=_SESSION_COOKIE),
    api_keys: ApiKeysContext = Depends(get_api_keys_context),
) -> ViewerSessionData:
    if not viewer_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    store = get_viewer_session_store()
    data = store.get(viewer_session)
    if data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    try:
        await api_keys.service.get_key_by_id(data.api_key_id)
    except ApiKeyInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key") from exc
    return data


async def _get_viewer_key(
    viewer_session: str | None = Cookie(None, alias=_SESSION_COOKIE),
    api_keys: ApiKeysContext = Depends(get_api_keys_context),
) -> ApiKeyData:
    session_data = await _get_viewer_session(viewer_session=viewer_session, api_keys=api_keys)
    try:
        return await api_keys.service.get_key_by_id(session_data.api_key_id)
    except ApiKeyInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key") from exc


@router.get("/logs", response_model=ViewerRequestLogsResponse)
async def list_logs(
    session_data: ViewerSessionData = Depends(_get_viewer_session),
    db: AsyncSession = Depends(get_session),
    limit: int = Query(50, ge=1, le=200),
    cursor: datetime | None = Query(None),
):
    service = ViewerPortalService(db)
    return await service.list_request_logs(session_data.api_key_id, limit=limit, cursor=cursor)


@router.get("/usage", response_model=ViewerUsageSummary)
async def get_usage(
    session_data: ViewerSessionData = Depends(_get_viewer_session),
    db: AsyncSession = Depends(get_session),
    since: datetime | None = Query(None),
):
    service = ViewerPortalService(db)
    return await service.get_usage_summary(session_data.api_key_id, since=since)


@router.get("/key-info", response_model=ViewerKeyInfo)
async def get_key_info(
    key_data: ApiKeyData = Depends(_get_viewer_key),
):
    return ViewerKeyInfo(key_id=key_data.id, key_name=key_data.name, is_active=key_data.is_active)


@router.get("/quota", response_model=list[ViewerQuotaEntry])
async def get_quota(
    session_data: ViewerSessionData = Depends(_get_viewer_session),
    db: AsyncSession = Depends(get_session),
):
    service = ViewerPortalService(db)
    return await service.get_quota(session_data.api_key_id)


@router.get("/trends", response_model=ApiKeyTrendsResponse)
async def get_trends(
    key_data: ApiKeyData = Depends(_get_viewer_key),
    api_keys: ApiKeysContext = Depends(get_api_keys_context),
) -> ApiKeyTrendsResponse:
    result = await api_keys.service.get_key_trends(key_data.id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return ApiKeyTrendsResponse(
        key_id=result.key_id,
        cost=[ApiKeyTrendPoint(t=point.t, v=point.v) for point in result.cost],
        tokens=[ApiKeyTrendPoint(t=point.t, v=point.v) for point in result.tokens],
    )


@router.get("/usage-7d", response_model=ApiKeyUsage7DayResponse)
async def get_usage_7d(
    key_data: ApiKeyData = Depends(_get_viewer_key),
    api_keys: ApiKeysContext = Depends(get_api_keys_context),
) -> ApiKeyUsage7DayResponse:
    result = await api_keys.service.get_key_usage_7d(key_data.id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return ApiKeyUsage7DayResponse(
        key_id=result.key_id,
        total_tokens=result.total_tokens,
        total_cost_usd=result.total_cost_usd,
        total_requests=result.total_requests,
        cached_input_tokens=result.cached_input_tokens,
        account_costs=[
            ApiKeyAccountCostResponse(
                account_id=account_cost.account_id,
                email=account_cost.email,
                cost_usd=account_cost.cost_usd,
                is_deleted=account_cost.is_deleted,
            )
            for account_cost in result.account_costs
        ],
    )
