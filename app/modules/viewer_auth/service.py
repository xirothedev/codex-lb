from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass, field

from app.modules.viewer_auth.schemas import ViewerSessionData

_SESSION_TTL_SECONDS = 3600 * 24  # 24 hours
_TOKEN_BYTES = 32


@dataclass(slots=True)
class _SessionEntry:
    data: ViewerSessionData
    expires_at: float


@dataclass(slots=True)
class ViewerSessionStore:
    _sessions: dict[str, _SessionEntry] = field(default_factory=dict)

    def create(self, session_data: ViewerSessionData) -> tuple[str, int]:
        token = secrets.token_hex(_TOKEN_BYTES)
        expires_at = time.monotonic() + _SESSION_TTL_SECONDS
        self._sessions[token] = _SessionEntry(data=session_data, expires_at=expires_at)
        return token, _SESSION_TTL_SECONDS

    def get(self, token: str) -> ViewerSessionData | None:
        entry = self._sessions.get(token)
        if entry is None:
            return None
        if time.monotonic() > entry.expires_at:
            del self._sessions[token]
            return None
        return entry.data

    def delete(self, token: str) -> None:
        self._sessions.pop(token, None)


_store = ViewerSessionStore()


def get_viewer_session_store() -> ViewerSessionStore:
    return _store


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()
