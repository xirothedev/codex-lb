from __future__ import annotations

from app.modules.viewer_auth.schemas import ViewerSessionData
from app.modules.viewer_auth.service import ViewerSessionStore


def test_viewer_session_store_round_trips_stateless_token() -> None:
    store = ViewerSessionStore()
    token, expires_in = store.create(ViewerSessionData(api_key_id="key-1"))

    assert expires_in > 0
    assert store.get(token) == ViewerSessionData(api_key_id="key-1")
    store.delete(token)
    assert store.get(token) == ViewerSessionData(api_key_id="key-1")


def test_viewer_session_store_rejects_invalid_token() -> None:
    store = ViewerSessionStore()

    assert store.get("not-a-valid-token") is None


def test_viewer_session_store_rejects_expired_token(monkeypatch) -> None:
    import app.modules.viewer_auth.service as viewer_service

    monkeypatch.setattr(viewer_service, "time", lambda: 1_000)
    store = ViewerSessionStore()
    token, expires_in = store.create(ViewerSessionData(api_key_id="key-1"))

    monkeypatch.setattr(viewer_service, "time", lambda: 1_000 + expires_in + 1)

    assert store.get(token) is None

