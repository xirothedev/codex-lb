from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, TypeAlias

import anyio
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.types import Receive, Send

from app.core.errors import openai_error
from app.core.metrics.prometheus import (
    proxy_endpoint_concurrency_in_flight,
    proxy_endpoint_concurrency_rejections_total,
)
from app.core.utils.request_id import get_request_id

logger = logging.getLogger(__name__)

ProxyRequestFamily: TypeAlias = Literal[
    "responses",
    "responses_compact",
    "chat_completions",
    "transcriptions",
    "models",
    "usage",
]

PROXY_REQUEST_FAMILIES: tuple[ProxyRequestFamily, ...] = (
    "responses",
    "responses_compact",
    "chat_completions",
    "transcriptions",
    "models",
    "usage",
)

DEFAULT_PROXY_ENDPOINT_CONCURRENCY_LIMITS: dict[ProxyRequestFamily, int] = {
    "responses": 0,
    "responses_compact": 0,
    "chat_completions": 0,
    "transcriptions": 0,
    "models": 0,
    "usage": 0,
}

_PATH_TO_FAMILY: dict[str, ProxyRequestFamily] = {
    "/backend-api/codex/responses": "responses",
    "/v1/responses": "responses",
    "/backend-api/codex/responses/compact": "responses_compact",
    "/v1/responses/compact": "responses_compact",
    "/v1/chat/completions": "chat_completions",
    "/backend-api/transcribe": "transcriptions",
    "/v1/audio/transcriptions": "transcriptions",
    "/backend-api/codex/models": "models",
    "/v1/models": "models",
    "/api/codex/usage": "usage",
    "/v1/usage": "usage",
}


def proxy_request_family_for_path(path: str) -> ProxyRequestFamily | None:
    normalized = path.rstrip("/") or "/"
    return _PATH_TO_FAMILY.get(normalized)


def proxy_endpoint_concurrency_limits_from_mapping(
    raw: Mapping[str, object] | None,
) -> dict[ProxyRequestFamily, int]:
    limits = DEFAULT_PROXY_ENDPOINT_CONCURRENCY_LIMITS.copy()
    if raw is None:
        return limits

    for family in PROXY_REQUEST_FAMILIES:
        value = raw.get(family)
        if isinstance(value, int) and value >= 0:
            limits[family] = value
    return limits


def build_proxy_endpoint_concurrency_error_response(
    request: Request,
    *,
    family: ProxyRequestFamily,
) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content=openai_error(
            "rate_limit_exceeded",
            _proxy_endpoint_concurrency_message(family),
            error_type="rate_limit_error",
        ),
        headers={"Retry-After": "5"},
    )


async def reject_proxy_endpoint_concurrency_websocket(
    receive: Receive,
    send: Send,
    *,
    family: ProxyRequestFamily,
) -> None:
    try:
        event = await receive()
        if event.get("type") != "websocket.connect":
            return
    except Exception:
        return

    await send(
        {
            "type": "websocket.close",
            "code": 1013,
            "reason": _proxy_endpoint_concurrency_message(family),
        }
    )


def record_proxy_endpoint_concurrency_rejection(
    *,
    family: ProxyRequestFamily,
    transport: str,
    method: str,
    path: str,
) -> None:
    logger.warning(
        "proxy_endpoint_concurrency_rejected request_id=%s family=%s transport=%s method=%s path=%s result=rejected",
        get_request_id(),
        family,
        transport,
        method,
        path,
    )
    if proxy_endpoint_concurrency_rejections_total is not None:
        proxy_endpoint_concurrency_rejections_total.labels(family=family, transport=transport).inc()


@dataclass(slots=True)
class ProxyEndpointConcurrencyLease:
    _limiter: "ProxyEndpointConcurrencyLimiter"
    family: ProxyRequestFamily
    _released: bool = False

    async def release(self) -> None:
        if self._released:
            return
        self._released = True
        await self._limiter.release(self.family)


class ProxyEndpointConcurrencyLimiter:
    def __init__(self) -> None:
        self._in_flight: dict[ProxyRequestFamily, int] = {
            family: 0 for family in PROXY_REQUEST_FAMILIES
        }
        self._lock = anyio.Lock()

    async def try_acquire(
        self,
        family: ProxyRequestFamily,
        *,
        limit: int,
    ) -> ProxyEndpointConcurrencyLease | None:
        if limit < 0:
            raise ValueError("limit must be non-negative")

        async with self._lock:
            current = self._in_flight[family]
            if limit > 0 and current >= limit:
                return None
            self._in_flight[family] = current + 1
            if proxy_endpoint_concurrency_in_flight is not None:
                proxy_endpoint_concurrency_in_flight.labels(family=family).inc()
        return ProxyEndpointConcurrencyLease(self, family)

    async def release(self, family: ProxyRequestFamily) -> None:
        async with self._lock:
            current = self._in_flight.get(family, 0)
            if current <= 0:
                return
            self._in_flight[family] = current - 1
            if proxy_endpoint_concurrency_in_flight is not None:
                proxy_endpoint_concurrency_in_flight.labels(family=family).dec()


def get_proxy_endpoint_concurrency_limiter() -> ProxyEndpointConcurrencyLimiter:
    return _proxy_endpoint_concurrency_limiter


def _proxy_endpoint_concurrency_message(family: ProxyRequestFamily) -> str:
    return f"Proxy endpoint concurrency limit exceeded for {family}"


_proxy_endpoint_concurrency_limiter = ProxyEndpointConcurrencyLimiter()


__all__ = [
    "DEFAULT_PROXY_ENDPOINT_CONCURRENCY_LIMITS",
    "PROXY_REQUEST_FAMILIES",
    "ProxyEndpointConcurrencyLease",
    "ProxyEndpointConcurrencyLimiter",
    "ProxyRequestFamily",
    "build_proxy_endpoint_concurrency_error_response",
    "get_proxy_endpoint_concurrency_limiter",
    "proxy_endpoint_concurrency_limits_from_mapping",
    "proxy_request_family_for_path",
    "record_proxy_endpoint_concurrency_rejection",
    "reject_proxy_endpoint_concurrency_websocket",
]
