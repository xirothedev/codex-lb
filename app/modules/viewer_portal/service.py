from __future__ import annotations

from datetime import datetime

from app.modules.api_keys.service import ApiKeysService
from app.modules.request_logs.service import (
    RequestLogFilterOptions,
    RequestLogModelOption,
    RequestLogsPage,
    RequestLogsService,
)


class ViewerPortalService:
    def __init__(self, api_keys_service: ApiKeysService, request_logs_service: RequestLogsService) -> None:
        self._api_keys = api_keys_service
        self._request_logs = request_logs_service

    async def get_api_key(self, api_key_id: str):
        return await self._api_keys.get_key_with_usage_summary_by_id(api_key_id)

    async def regenerate_key(self, api_key_id: str):
        return await self._api_keys.regenerate_key(api_key_id)

    async def list_request_logs(
        self,
        *,
        api_key_id: str,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        model_options: list[RequestLogModelOption] | None = None,
        models: list[str] | None = None,
        reasoning_efforts: list[str] | None = None,
        status: list[str] | None = None,
    ) -> RequestLogsPage:
        return await self._request_logs.list_recent(
            limit=limit,
            offset=offset,
            search=search,
            since=since,
            until=until,
            api_key_ids=[api_key_id],
            model_options=model_options,
            models=models,
            reasoning_efforts=reasoning_efforts,
            status=status,
        )

    async def list_request_log_options(
        self,
        *,
        api_key_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
        model_options: list[RequestLogModelOption] | None = None,
        models: list[str] | None = None,
        reasoning_efforts: list[str] | None = None,
    ) -> RequestLogFilterOptions:
        return await self._request_logs.list_filter_options(
            since=since,
            until=until,
            api_key_ids=[api_key_id],
            model_options=model_options,
            models=models,
            reasoning_efforts=reasoning_efforts,
        )
