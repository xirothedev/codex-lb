from __future__ import annotations

import json
from dataclasses import dataclass
from time import time

from app.core.crypto import TokenEncryptor
from app.core.exceptions import DashboardAuthError
from app.modules.api_keys.schemas import ApiKeyUsageSummaryResponse, LimitRuleResponse
from app.modules.api_keys.service import ApiKeyCreatedData, ApiKeyData, ApiKeyInvalidError, ApiKeysService
from app.modules.viewer_auth.schemas import (
    ViewerApiKeyRegenerateResponse,
    ViewerApiKeyResponse,
    ViewerAuthSessionResponse,
)

VIEWER_SESSION_COOKIE = "codex_lb_viewer_session"
VIEWER_SESSION_TTL_SECONDS = 12 * 60 * 60


@dataclass(slots=True)
class ViewerSessionState:
    expires_at: int
    api_key_id: str
    key_prefix: str


class ViewerSessionStore:
    def __init__(self) -> None:
        self._encryptor: TokenEncryptor | None = None

    def _get_encryptor(self) -> TokenEncryptor:
        if self._encryptor is None:
            self._encryptor = TokenEncryptor()
        return self._encryptor

    def create(self, *, api_key_id: str, key_prefix: str) -> str:
        expires_at = int(time()) + VIEWER_SESSION_TTL_SECONDS
        payload = json.dumps(
            {"exp": expires_at, "kid": api_key_id, "kp": key_prefix},
            separators=(",", ":"),
        )
        return self._get_encryptor().encrypt(payload).decode("ascii")

    def get(self, session_id: str | None) -> ViewerSessionState | None:
        if not session_id:
            return None
        token = session_id.strip()
        if not token:
            return None
        try:
            raw = self._get_encryptor().decrypt(token.encode("ascii"))
            data = json.loads(raw)
        except Exception:
            return None
        exp = data.get("exp")
        api_key_id = data.get("kid")
        key_prefix = data.get("kp")
        if not isinstance(exp, int) or not isinstance(api_key_id, str) or not isinstance(key_prefix, str):
            return None
        if exp < int(time()):
            return None
        return ViewerSessionState(expires_at=exp, api_key_id=api_key_id, key_prefix=key_prefix)


class ViewerAuthService:
    def __init__(self, api_keys_service: ApiKeysService, session_store: ViewerSessionStore) -> None:
        self._api_keys = api_keys_service
        self._session_store = session_store

    async def login(self, plain_key: str) -> tuple[str, ViewerAuthSessionResponse]:
        api_key = await self._api_keys.validate_key(plain_key.strip())
        session_id = self._session_store.create(api_key_id=api_key.id, key_prefix=api_key.key_prefix)
        return session_id, _session_response(api_key)

    async def get_session_state(self, session_id: str | None) -> ViewerAuthSessionResponse:
        state = self._session_store.get(session_id)
        if state is None:
            return ViewerAuthSessionResponse(authenticated=False)
        try:
            api_key = await self._api_keys.get_key_by_id(state.api_key_id)
        except ApiKeyInvalidError:
            return ViewerAuthSessionResponse(authenticated=False)
        if api_key.key_prefix != state.key_prefix:
            return ViewerAuthSessionResponse(authenticated=False)
        return _session_response(api_key)

    async def regenerate_authenticated_key(
        self,
        session_id: str | None,
    ) -> tuple[str, ViewerApiKeyRegenerateResponse]:
        state = self.require_session(session_id)
        created = await self._api_keys.regenerate_key(state.api_key_id)
        next_session_id = self._session_store.create(api_key_id=created.id, key_prefix=created.key_prefix)
        return next_session_id, _regenerate_response(created)

    def logout(self, session_id: str | None) -> None:
        _ = session_id
        return

    def require_session(self, session_id: str | None) -> ViewerSessionState:
        state = self._session_store.get(session_id)
        if state is None:
            raise DashboardAuthError("Authentication is required")
        return state


def _session_response(api_key: ApiKeyData) -> ViewerAuthSessionResponse:
    return ViewerAuthSessionResponse(
        authenticated=True,
        api_key=_to_viewer_api_key_response(api_key),
        can_regenerate=True,
    )


def _regenerate_response(api_key: ApiKeyCreatedData) -> ViewerApiKeyRegenerateResponse:
    base = _to_viewer_api_key_response(api_key)
    return ViewerApiKeyRegenerateResponse(**base.model_dump(), key=api_key.key)


def _to_viewer_api_key_response(api_key: ApiKeyData) -> ViewerApiKeyResponse:
    return ViewerApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        masked_key=_masked_key(api_key.key_prefix),
        allowed_models=api_key.allowed_models,
        enforced_model=api_key.enforced_model,
        enforced_reasoning_effort=api_key.enforced_reasoning_effort,
        expires_at=api_key.expires_at,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        limits=[
            LimitRuleResponse(
                id=limit.id,
                limit_type=limit.limit_type,
                limit_window=limit.limit_window,
                max_value=limit.max_value,
                current_value=limit.current_value,
                model_filter=limit.model_filter,
                reset_at=limit.reset_at,
            )
            for limit in api_key.limits
        ],
        usage_summary=(
            ApiKeyUsageSummaryResponse(
                request_count=api_key.usage_summary.request_count,
                total_tokens=api_key.usage_summary.total_tokens,
                cached_input_tokens=api_key.usage_summary.cached_input_tokens,
                total_cost_usd=api_key.usage_summary.total_cost_usd,
            )
            if api_key.usage_summary is not None
            else None
        ),
    )


def _masked_key(key_prefix: str) -> str:
    return f"{key_prefix}..."


_viewer_session_store: ViewerSessionStore | None = None


def get_viewer_session_store() -> ViewerSessionStore:
    global _viewer_session_store
    if _viewer_session_store is None:
        _viewer_session_store = ViewerSessionStore()
    return _viewer_session_store
