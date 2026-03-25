from __future__ import annotations

from app.modules.viewer_auth.service import ViewerSessionStore


def test_viewer_session_store_round_trip():
    store = ViewerSessionStore()

    token = store.create(api_key_id="key_123", key_prefix="sk-clb-test")
    state = store.get(token)

    assert state is not None
    assert state.api_key_id == "key_123"
    assert state.key_prefix == "sk-clb-test"
    assert state.expires_at > 0


def test_viewer_session_store_rejects_invalid_payload():
    store = ViewerSessionStore()

    assert store.get("not-a-real-token") is None
