from __future__ import annotations

from datetime import datetime, timedelta

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ApiKeyLimit, RequestLog
from app.modules.viewer_portal.schemas import (
    ViewerQuotaEntry,
    ViewerRequestLogEntry,
    ViewerRequestLogsResponse,
    ViewerUsageSummary,
)


class ViewerPortalService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_request_logs(
        self,
        api_key_id: str,
        *,
        limit: int = 50,
        cursor: datetime | None = None,
    ) -> ViewerRequestLogsResponse:
        base = (
            sa.select(RequestLog)
            .where(
                RequestLog.api_key_id == api_key_id,
                RequestLog.deleted_at.is_(None),
            )
            .order_by(RequestLog.requested_at.desc())
        )
        if cursor:
            base = base.where(RequestLog.requested_at < cursor)

        result = await self._session.execute(base.limit(limit + 1))
        rows = result.scalars().all()
        has_more = len(rows) > limit
        entries = rows[:limit]

        count_result = await self._session.execute(
            sa.select(sa.func.count())
            .select_from(RequestLog)
            .where(RequestLog.api_key_id == api_key_id, RequestLog.deleted_at.is_(None))
        )
        total = count_result.scalar() or 0

        return ViewerRequestLogsResponse(
            requests=[
                ViewerRequestLogEntry(
                    requested_at=r.requested_at,
                    request_id=r.request_id,
                    model=r.model,
                    status=r.status,
                    input_tokens=r.input_tokens,
                    output_tokens=r.output_tokens,
                    cached_input_tokens=r.cached_input_tokens,
                    cost_usd=r.cost_usd,
                    latency_ms=r.latency_ms,
                    latency_first_token_ms=r.latency_first_token_ms,
                )
                for r in entries
            ],
            total=total,
            has_more=has_more,
        )

    async def get_usage_summary(
        self,
        api_key_id: str,
        *,
        since: datetime | None = None,
    ) -> ViewerUsageSummary:
        since = since or (datetime.utcnow() - timedelta(days=7))
        filters = [
            RequestLog.api_key_id == api_key_id,
            RequestLog.deleted_at.is_(None),
            RequestLog.requested_at >= since,
        ]
        base = sa.select(RequestLog).where(*filters)
        result = await self._session.execute(base)
        rows = result.scalars().all()

        total = len(rows)
        successful = sum(1 for r in rows if r.status == "success")
        total_input = sum(r.input_tokens or 0 for r in rows)
        total_output = sum(r.output_tokens or 0 for r in rows)
        total_cached = sum(r.cached_input_tokens or 0 for r in rows)
        total_cost = sum(r.cost_usd or 0.0 for r in rows)
        latencies = [r.latency_ms for r in rows if r.latency_ms is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else None

        return ViewerUsageSummary(
            total_requests=total,
            successful_requests=successful,
            failed_requests=total - successful,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_cached_input_tokens=total_cached,
            total_cost_usd=round(total_cost, 6),
            avg_latency_ms=round(avg_latency, 1) if avg_latency else None,
        )

    async def get_quota(self, api_key_id: str) -> list[ViewerQuotaEntry]:
        result = await self._session.execute(
            sa.select(ApiKeyLimit).where(
                ApiKeyLimit.api_key_id == api_key_id,
            )
        )
        limits = result.scalars().all()
        return [
            ViewerQuotaEntry(
                limit_type=l.limit_type.value,
                limit_window=l.limit_window.value,
                max_value=l.max_value,
                current_value=l.current_value,
                reset_at=l.reset_at,
            )
            for l in limits
        ]
