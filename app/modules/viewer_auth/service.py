from __future__ import annotations

import json
from dataclasses import dataclass
from time import time

from app.core.crypto import TokenEncryptor
from app.modules.viewer_auth.schemas import ViewerSessionData

_SESSION_TTL_SECONDS = 3600 * 24  # 24 hours


@dataclass(slots=True)
class ViewerSessionStore:
    _encryptor: TokenEncryptor | None = None

    def _get_encryptor(self) -> TokenEncryptor:
        if self._encryptor is None:
            self._encryptor = TokenEncryptor()
        return self._encryptor

    def create(self, session_data: ViewerSessionData) -> tuple[str, int]:
        expires_at = int(time()) + _SESSION_TTL_SECONDS
        payload = json.dumps(
            {"exp": expires_at, "kid": session_data.api_key_id},
            separators=(",", ":"),
        )
        token = self._get_encryptor().encrypt(payload).decode("ascii")
        return token, _SESSION_TTL_SECONDS

    def get(self, token: str) -> ViewerSessionData | None:
        stripped = token.strip()
        if not stripped:
            return None
        try:
            raw = self._get_encryptor().decrypt(stripped.encode("ascii"))
            payload = json.loads(raw)
        except Exception:
            return None

        expires_at = payload.get("exp")
        api_key_id = payload.get("kid")
        if not isinstance(expires_at, int) or not isinstance(api_key_id, str) or not api_key_id:
            return None
        if expires_at < int(time()):
            return None
        return ViewerSessionData(api_key_id=api_key_id)

    def delete(self, token: str) -> None:
        # Stateless: deletion is handled by clearing the cookie client-side.
        return


_store = ViewerSessionStore()


def get_viewer_session_store() -> ViewerSessionStore:
    return _store
