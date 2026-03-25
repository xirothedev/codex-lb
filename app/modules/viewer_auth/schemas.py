from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.modules.api_keys.schemas import ApiKeyUsageSummaryResponse, LimitRuleResponse
from app.modules.shared.schemas import DashboardModel


class ViewerApiKeyResponse(DashboardModel):
    id: str
    name: str
    key_prefix: str
    masked_key: str
    allowed_models: list[str] | None
    enforced_model: str | None
    enforced_reasoning_effort: str | None
    expires_at: datetime | None
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None
    limits: list[LimitRuleResponse] = Field(default_factory=list)
    usage_summary: ApiKeyUsageSummaryResponse | None = None


class ViewerAuthSessionResponse(DashboardModel):
    authenticated: bool
    api_key: ViewerApiKeyResponse | None = None
    can_regenerate: bool = False


class ViewerLoginRequest(DashboardModel):
    api_key: str


class ViewerApiKeyRegenerateResponse(ViewerApiKeyResponse):
    key: str
