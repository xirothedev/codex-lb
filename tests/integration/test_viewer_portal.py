from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.db.models import Account, RequestLog
from app.db.session import SessionLocal
from app.modules.viewer_auth.service import ViewerSessionStore

pytestmark = pytest.mark.integration


async def _create_api_key(async_client, *, name: str) -> dict:
    response = await async_client.post("/api/api-keys/", json={"name": name})
    assert response.status_code == 200
    return response.json()


async def _insert_request_logs(*rows: RequestLog) -> None:
    async with SessionLocal() as session:
        session.add_all(rows)
        await session.commit()


@pytest.mark.asyncio
async def test_viewer_cookie_survives_process_local_store_reset(
    async_client,
    monkeypatch: pytest.MonkeyPatch,
):
    created = await _create_api_key(async_client, name="viewer-key")
    login = await async_client.post("/viewer/auth/login", json={"api_key": created["key"]})
    assert login.status_code == 200

    import app.modules.viewer_auth.service as viewer_service

    monkeypatch.setattr(viewer_service, "_store", ViewerSessionStore())

    response = await async_client.get("/viewer/key-info")

    assert response.status_code == 200
    assert response.json()["key_id"] == created["id"]
    assert response.json()["key_name"] == "viewer-key"


@pytest.mark.asyncio
async def test_viewer_rejects_invalid_session_cookie(async_client):
    async_client.cookies.set("viewer_session", "invalid-token", path="/viewer")

    response = await async_client.get("/viewer/key-info")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_viewer_rejects_inactive_api_key_after_login(async_client):
    created = await _create_api_key(async_client, name="viewer-inactive-key")
    login = await async_client.post("/viewer/auth/login", json={"api_key": created["key"]})
    assert login.status_code == 200

    updated = await async_client.patch(f"/api/api-keys/{created['id']}", json={"isActive": False})
    assert updated.status_code == 200

    response = await async_client.get("/viewer/key-info")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_viewer_usage_graph_endpoints_are_scoped_to_logged_in_key(
    async_client,
    monkeypatch: pytest.MonkeyPatch,
):
    first = await _create_api_key(async_client, name="viewer-graph-key")
    second = await _create_api_key(async_client, name="other-graph-key")
    login = await async_client.post("/viewer/auth/login", json={"api_key": first["key"]})
    assert login.status_code == 200

    now = datetime(2026, 5, 27, 12, 0, 0)
    monkeypatch.setattr("app.modules.api_keys.service.utcnow", lambda: now)
    await _insert_request_logs(
        Account(
            id="viewer-account-secret",
            email="secret-account@example.com",
            plan_type="plus",
            access_token_encrypted=b"access",
            refresh_token_encrypted=b"refresh",
            id_token_encrypted=b"id",
            last_refresh=now,
        ),
        RequestLog(
            account_id="viewer-account-secret",
            api_key_id=first["id"],
            request_id="viewer-req",
            requested_at=now - timedelta(hours=1),
            model="gpt-5.3-codex",
            status="success",
            input_tokens=20,
            output_tokens=10,
            cached_input_tokens=5,
            cost_usd=1.25,
        ),
        RequestLog(
            api_key_id=second["id"],
            request_id="other-req",
            requested_at=now - timedelta(hours=1),
            model="gpt-5.3-codex",
            status="success",
            input_tokens=200,
            output_tokens=100,
            cached_input_tokens=50,
            cost_usd=12.5,
        ),
    )

    usage = await async_client.get("/viewer/usage-7d")
    trends = await async_client.get("/viewer/trends")

    assert usage.status_code == 200
    usage_payload = usage.json()
    assert usage_payload["keyId"] == first["id"]
    assert usage_payload["totalRequests"] == 1
    assert usage_payload["totalTokens"] == 30
    assert usage_payload["totalCostUsd"] == pytest.approx(1.25)
    assert usage_payload["accountCosts"] == []
    assert "secret-account@example.com" not in usage.text
    assert "viewer-account-secret" not in usage.text

    assert trends.status_code == 200
    trends_payload = trends.json()
    assert trends_payload["keyId"] == first["id"]
    assert sum(point["v"] for point in trends_payload["tokens"]) == pytest.approx(30)
    assert sum(point["v"] for point in trends_payload["cost"]) == pytest.approx(1.25)


@pytest.mark.asyncio
async def test_viewer_logs_are_page_paginated_and_scoped_to_logged_in_key(async_client):
    first = await _create_api_key(async_client, name="viewer-logs-key")
    second = await _create_api_key(async_client, name="other-logs-key")
    login = await async_client.post("/viewer/auth/login", json={"api_key": first["key"]})
    assert login.status_code == 200

    now = datetime(2026, 5, 27, 12, 0, 0)
    await _insert_request_logs(
        *[
            RequestLog(
                api_key_id=first["id"],
                request_id=f"viewer-req-{index}",
                requested_at=now - timedelta(minutes=index),
                model="gpt-5.3-codex",
                status="success",
                input_tokens=10 + index,
                output_tokens=20 + index,
                cost_usd=0.1 + index,
            )
            for index in range(5)
        ],
        RequestLog(
            api_key_id=second["id"],
            request_id="other-req",
            requested_at=now,
            model="gpt-5.3-codex",
            status="success",
            input_tokens=999,
            output_tokens=999,
            cost_usd=99,
        ),
    )

    response = await async_client.get("/viewer/logs?page=2&page_size=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 5
    assert payload["page"] == 2
    assert payload["page_size"] == 2
    assert payload["total_pages"] == 3
    assert payload["has_next"] is True
    assert payload["has_previous"] is True
    assert [row["request_id"] for row in payload["requests"]] == ["viewer-req-2", "viewer-req-3"]
    assert "other-req" not in response.text
