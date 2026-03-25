from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import SessionLocal
from app.main import create_app
from app.modules.request_logs.repository import RequestLogsRepository

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_viewer_login_metadata_and_regeneration(async_client):
    created = await async_client.post(
        "/api/api-keys/",
        json={"name": "viewer-key"},
    )
    assert created.status_code == 200
    payload = created.json()
    original_key = payload["key"]

    login = await async_client.post("/api/viewer-auth/login", json={"apiKey": original_key})
    assert login.status_code == 200
    login_payload = login.json()
    assert login_payload["authenticated"] is True
    assert login_payload["apiKey"]["id"] == payload["id"]
    assert login_payload["apiKey"]["maskedKey"].startswith(login_payload["apiKey"]["keyPrefix"])
    assert login_payload["apiKey"]["createdAt"].endswith("Z")
    assert "key" not in login_payload["apiKey"]

    viewer_key = await async_client.get("/api/viewer/api-key")
    assert viewer_key.status_code == 200
    viewer_payload = viewer_key.json()
    assert viewer_payload["id"] == payload["id"]
    assert viewer_payload["maskedKey"].startswith(viewer_payload["keyPrefix"])
    assert "key" not in viewer_payload

    regenerated = await async_client.post("/api/viewer/api-key/regenerate")
    assert regenerated.status_code == 200
    regenerated_payload = regenerated.json()
    assert regenerated_payload["id"] == payload["id"]
    assert regenerated_payload["key"].startswith("sk-clb-")
    assert regenerated_payload["key"] != original_key
    assert regenerated_payload["createdAt"].endswith("Z")

    still_authenticated = await async_client.get("/api/viewer/api-key")
    assert still_authenticated.status_code == 200
    assert still_authenticated.json()["keyPrefix"] == regenerated_payload["keyPrefix"]

    old_login = await async_client.post("/api/viewer-auth/login", json={"apiKey": original_key})
    assert old_login.status_code == 401

    new_login = await async_client.post("/api/viewer-auth/login", json={"apiKey": regenerated_payload["key"]})
    assert new_login.status_code == 200
    assert new_login.json()["authenticated"] is True

    stale_client = AsyncClient(
        transport=ASGITransport(app=create_app()),
        base_url="http://testserver",
        cookies={"codex_lb_viewer_session": login.cookies.get("codex_lb_viewer_session", "")},
    )
    async with stale_client:
        stale_view = await stale_client.get("/api/viewer/api-key")
    assert stale_view.status_code == 401


@pytest.mark.asyncio
async def test_viewer_request_logs_are_scoped_and_scrubbed(async_client):
    created_a = await async_client.post("/api/api-keys/", json={"name": "viewer-a"})
    created_b = await async_client.post("/api/api-keys/", json={"name": "viewer-b"})
    assert created_a.status_code == 200
    assert created_b.status_code == 200

    key_a = created_a.json()
    key_b = created_b.json()

    async with SessionLocal() as session:
        repo = RequestLogsRepository(session)
        await repo.add_log(
            account_id=None,
            api_key_id=key_a["id"],
            request_id="req_viewer_a",
            model="gpt-5.1",
            input_tokens=11,
            output_tokens=7,
            latency_ms=120,
            status="success",
            error_code=None,
        )
        await repo.add_log(
            account_id=None,
            api_key_id=key_b["id"],
            request_id="req_viewer_b",
            model="gpt-4o-mini",
            input_tokens=5,
            output_tokens=3,
            latency_ms=80,
            status="success",
            error_code=None,
        )

    login = await async_client.post("/api/viewer-auth/login", json={"apiKey": key_a["key"]})
    assert login.status_code == 200

    logs = await async_client.get("/api/viewer/request-logs")
    assert logs.status_code == 200
    log_payload = logs.json()
    assert log_payload["total"] == 1
    assert log_payload["requests"][0]["requestId"] == "req_viewer_a"
    assert log_payload["requests"][0]["accountId"] is None
    assert log_payload["requests"][0]["apiKeyName"] is None

    options = await async_client.get("/api/viewer/request-logs/options")
    assert options.status_code == 200
    options_payload = options.json()
    assert options_payload["accountIds"] == []
    assert options_payload["statuses"] == ["ok"]
