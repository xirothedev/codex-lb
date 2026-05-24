from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ViewerRequestLogEntry(BaseModel):
    requested_at: datetime
    request_id: str
    model: str
    status: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_input_tokens: int | None = None
    cost_usd: float | None = None
    latency_ms: int | None = None
    latency_first_token_ms: int | None = None


class ViewerRequestLogsResponse(BaseModel):
    requests: list[ViewerRequestLogEntry]
    total: int
    has_more: bool


class ViewerUsageSummary(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cached_input_tokens: int
    total_cost_usd: float
    avg_latency_ms: float | None = None


class ViewerKeyInfo(BaseModel):
    key_name: str
    is_active: bool
