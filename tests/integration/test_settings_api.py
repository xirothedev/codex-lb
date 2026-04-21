from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_settings_api_get_and_update(async_client):
    response = await async_client.get("/api/settings")
    assert response.status_code == 200
    payload = response.json()
    assert payload["stickyThreadsEnabled"] is True
    assert payload["upstreamStreamTransport"] == "default"
    assert payload["preferEarlierResetAccounts"] is True
    assert payload["routingStrategy"] == "capacity_weighted"
    assert payload["openaiCacheAffinityMaxAgeSeconds"] == 1800
    assert payload["httpResponsesSessionBridgePromptCacheIdleTtlSeconds"] == 3600
    assert payload["httpResponsesSessionBridgeGatewaySafeMode"] is False
    assert payload["stickyReallocationBudgetThresholdPct"] == 95.0
    assert payload["importWithoutOverwrite"] is True
    assert payload["totpRequiredOnLogin"] is False
    assert payload["totpConfigured"] is False
    assert payload["apiKeyAuthEnabled"] is False
    assert payload["proxyEndpointConcurrencyLimits"] == {
        "responses": 0,
        "responses_compact": 0,
        "chat_completions": 0,
        "transcriptions": 0,
        "models": 0,
        "usage": 0,
    }

    response = await async_client.put(
        "/api/settings",
        json={
            "stickyThreadsEnabled": False,
            "upstreamStreamTransport": "websocket",
            "preferEarlierResetAccounts": False,
            "routingStrategy": "round_robin",
            "openaiCacheAffinityMaxAgeSeconds": 180,
            "httpResponsesSessionBridgePromptCacheIdleTtlSeconds": 1800,
            "httpResponsesSessionBridgeGatewaySafeMode": True,
            "stickyReallocationBudgetThresholdPct": 90.0,
            "importWithoutOverwrite": False,
            "totpRequiredOnLogin": False,
            "apiKeyAuthEnabled": True,
            "proxyEndpointConcurrencyLimits": {
                "responses": 1,
                "responses_compact": 2,
                "chat_completions": 3,
                "transcriptions": 4,
                "models": 5,
                "usage": 6,
            },
        },
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["stickyThreadsEnabled"] is False
    assert updated["upstreamStreamTransport"] == "websocket"
    assert updated["preferEarlierResetAccounts"] is False
    assert updated["routingStrategy"] == "round_robin"
    assert updated["openaiCacheAffinityMaxAgeSeconds"] == 180
    assert updated["httpResponsesSessionBridgePromptCacheIdleTtlSeconds"] == 1800
    assert updated["httpResponsesSessionBridgeGatewaySafeMode"] is True
    assert updated["stickyReallocationBudgetThresholdPct"] == 90.0
    assert updated["importWithoutOverwrite"] is False
    assert updated["totpRequiredOnLogin"] is False
    assert updated["totpConfigured"] is False
    assert updated["apiKeyAuthEnabled"] is True
    assert updated["proxyEndpointConcurrencyLimits"] == {
        "responses": 1,
        "responses_compact": 2,
        "chat_completions": 3,
        "transcriptions": 4,
        "models": 5,
        "usage": 6,
    }

    response = await async_client.get("/api/settings")
    assert response.status_code == 200
    payload = response.json()
    assert payload["stickyThreadsEnabled"] is False
    assert payload["upstreamStreamTransport"] == "websocket"
    assert payload["preferEarlierResetAccounts"] is False
    assert payload["routingStrategy"] == "round_robin"
    assert payload["openaiCacheAffinityMaxAgeSeconds"] == 180
    assert payload["httpResponsesSessionBridgePromptCacheIdleTtlSeconds"] == 1800
    assert payload["httpResponsesSessionBridgeGatewaySafeMode"] is True
    assert payload["stickyReallocationBudgetThresholdPct"] == 90.0
    assert payload["importWithoutOverwrite"] is False
    assert payload["totpRequiredOnLogin"] is False
    assert payload["totpConfigured"] is False
    assert payload["apiKeyAuthEnabled"] is True
    assert payload["proxyEndpointConcurrencyLimits"] == {
        "responses": 1,
        "responses_compact": 2,
        "chat_completions": 3,
        "transcriptions": 4,
        "models": 5,
        "usage": 6,
    }


@pytest.mark.asyncio
async def test_settings_api_rejects_invalid_proxy_endpoint_concurrency_limits(async_client):
    response = await async_client.put(
        "/api/settings",
        json={
            "stickyThreadsEnabled": True,
            "preferEarlierResetAccounts": True,
            "proxyEndpointConcurrencyLimits": {
                "responses": -1,
                "responses_compact": 0,
                "chat_completions": 0,
                "transcriptions": 0,
                "models": 0,
                "usage": 0,
            },
        },
    )

    assert response.status_code == 422
