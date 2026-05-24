from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.modules.viewer_auth.schemas import ViewerSessionData
from app.modules.viewer_auth.service import get_viewer_session_store
from app.modules.viewer_portal.schemas import ViewerKeyInfo, ViewerRequestLogsResponse, ViewerUsageSummary
from app.modules.viewer_portal.service import ViewerPortalService

router = APIRouter(prefix="/viewer", tags=["viewer-portal"])

_SESSION_COOKIE = "viewer_session"


async def _get_viewer_session(
    viewer_session: str | None = Cookie(None, alias=_SESSION_COOKIE),
) -> ViewerSessionData:
    if not viewer_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    store = get_viewer_session_store()
    data = store.get(viewer_session)
    if data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    return data


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
    session_data: ViewerSessionData = Depends(_get_viewer_session),
):
    return ViewerKeyInfo(key_name=session_data.key_name, is_active=session_data.is_active)
