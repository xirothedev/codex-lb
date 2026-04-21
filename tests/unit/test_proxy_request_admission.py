from __future__ import annotations

import json

import pytest
from starlette.requests import Request

from app.modules.proxy.request_admission import (
    DEFAULT_PROXY_ENDPOINT_CONCURRENCY_LIMITS,
    ProxyEndpointConcurrencyLimiter,
    build_proxy_endpoint_concurrency_error_response,
    proxy_request_family_for_path,
    reject_proxy_endpoint_concurrency_websocket,
)

pytestmark = pytest.mark.unit


def test_proxy_request_family_maps_aliases_and_bypasses_internal_bridge() -> None:
    assert proxy_request_family_for_path("/v1/responses") == "responses"
    assert proxy_request_family_for_path("/backend-api/codex/responses") == "responses"
    assert proxy_request_family_for_path("/v1/responses/compact") == "responses_compact"
    assert proxy_request_family_for_path("/backend-api/codex/responses/compact") == "responses_compact"
    assert proxy_request_family_for_path("/v1/chat/completions") == "chat_completions"
    assert proxy_request_family_for_path("/backend-api/transcribe") == "transcriptions"
    assert proxy_request_family_for_path("/v1/audio/transcriptions") == "transcriptions"
    assert proxy_request_family_for_path("/backend-api/codex/models") == "models"
    assert proxy_request_family_for_path("/v1/models") == "models"
    assert proxy_request_family_for_path("/api/codex/usage") == "usage"
    assert proxy_request_family_for_path("/v1/usage") == "usage"
    assert proxy_request_family_for_path("/internal/bridge/responses") is None
    assert proxy_request_family_for_path("/api/settings") is None


@pytest.mark.asyncio
async def test_proxy_request_limiter_rejects_when_shared_family_is_full() -> None:
    limiter = ProxyEndpointConcurrencyLimiter()

    first = await limiter.try_acquire("responses", limit=1)
    assert first is not None

    second = await limiter.try_acquire("responses", limit=1)
    assert second is None

    await first.release()

    third = await limiter.try_acquire("responses", limit=1)
    assert third is not None
    await third.release()


@pytest.mark.asyncio
async def test_proxy_request_limiter_isolates_different_families_and_supports_unlimited() -> None:
    limiter = ProxyEndpointConcurrencyLimiter()

    responses = await limiter.try_acquire("responses", limit=1)
    chat = await limiter.try_acquire("chat_completions", limit=1)
    usage_one = await limiter.try_acquire("usage", limit=0)
    usage_two = await limiter.try_acquire("usage", limit=0)

    assert responses is not None
    assert chat is not None
    assert usage_one is not None
    assert usage_two is not None

    await responses.release()
    await chat.release()
    await usage_one.release()
    await usage_two.release()


def test_build_proxy_endpoint_concurrency_error_response_returns_openai_429() -> None:
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/v1/responses",
            "headers": [],
        }
    )

    response = build_proxy_endpoint_concurrency_error_response(request, family="responses")

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "5"
    payload = json.loads(response.body.decode("utf-8"))
    assert payload == {
        "error": {
            "code": "rate_limit_exceeded",
            "message": "Proxy endpoint concurrency limit exceeded for responses",
            "type": "rate_limit_error",
        }
    }


@pytest.mark.asyncio
async def test_reject_proxy_endpoint_concurrency_websocket_closes_with_1013() -> None:
    sent_events: list[dict[str, object]] = []
    connect_delivered = False

    async def receive() -> dict[str, object]:
        nonlocal connect_delivered
        if not connect_delivered:
            connect_delivered = True
            return {"type": "websocket.connect"}
        return {"type": "websocket.disconnect", "code": 1000}

    async def send(message: dict[str, object]) -> None:
        sent_events.append(message)

    await reject_proxy_endpoint_concurrency_websocket(receive, send, family="responses")

    assert sent_events == [
        {
            "type": "websocket.close",
            "code": 1013,
            "reason": "Proxy endpoint concurrency limit exceeded for responses",
        }
    ]


def test_default_proxy_endpoint_concurrency_limits_cover_all_families() -> None:
    assert DEFAULT_PROXY_ENDPOINT_CONCURRENCY_LIMITS == {
        "responses": 0,
        "responses_compact": 0,
        "chat_completions": 0,
        "transcriptions": 0,
        "models": 0,
        "usage": 0,
    }
