from __future__ import annotations

import contextlib
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

import app.core.auth.refresh as refresh_module
import app.core.clients.model_fetcher as model_fetcher_module
import app.core.openai.model_refresh_scheduler as scheduler_module
from app.core.crypto import TokenEncryptor
from app.core.openai.model_registry import ReasoningLevel, UpstreamModel
from app.db.models import Account, AccountStatus
from app.modules.accounts.runtime_health import PAUSE_REASON_MODEL_REFRESH

pytestmark = pytest.mark.unit


def _make_account(account_id: str) -> Account:
    encryptor = TokenEncryptor()
    return Account(
        id=account_id,
        chatgpt_account_id=account_id,
        email=f"{account_id}@example.com",
        plan_type="plus",
        access_token_encrypted=encryptor.encrypt("access-token"),
        refresh_token_encrypted=encryptor.encrypt("refresh-token"),
        id_token_encrypted=encryptor.encrypt("id-token"),
        last_refresh=datetime.now(tz=timezone.utc),
        status=AccountStatus.ACTIVE,
        deactivation_reason=None,
    )


def _account(account_id: str = "account-1") -> Account:
    return Account(
        id=account_id,
        email=f"{account_id}@example.test",
        plan_type="team",
        chatgpt_account_id=f"chatgpt-{account_id}",
        access_token_encrypted=b"encrypted-access-token",
        refresh_token_encrypted=b"encrypted-refresh-token",
        id_token_encrypted=b"encrypted-id-token",
        last_refresh=datetime(2026, 1, 1),
        status=AccountStatus.ACTIVE,
    )


def _model(slug: str) -> UpstreamModel:
    return UpstreamModel(
        slug=slug,
        display_name=slug,
        description=f"Model {slug}",
        context_window=128000,
        input_modalities=("text",),
        supported_reasoning_levels=(ReasoningLevel(effort="medium", description="balanced"),),
        default_reasoning_level="medium",
        supports_reasoning_summaries=False,
        support_verbosity=False,
        default_verbosity=None,
        prefer_websockets=False,
        supports_parallel_tool_calls=True,
        supported_in_api=True,
        minimal_client_version=None,
        priority=0,
        available_in_plans=frozenset(),
        raw={},
    )


def _make_model(slug: str) -> UpstreamModel:
    return _model(slug)


class _StubAccountsRepository:
    def __init__(self) -> None:
        self.status_updates: list[dict[str, object]] = []

    async def update_status(
        self,
        account_id: str,
        status: AccountStatus,
        deactivation_reason: str | None = None,
        reset_at: int | None = None,
    ) -> bool:
        self.status_updates.append(
            {
                "account_id": account_id,
                "status": status,
                "deactivation_reason": deactivation_reason,
                "reset_at": reset_at,
            }
        )
        return True

    async def get_by_id(self, account_id: str) -> Account | None:  # pragma: no cover - protocol completeness
        return None

    async def update_tokens(self, *args, **kwargs) -> bool:  # pragma: no cover - protocol completeness
        return True


@pytest.mark.asyncio
async def test_fetch_with_failover_pauses_401_account_and_uses_next_candidate(monkeypatch) -> None:
    first = _make_account("acc_model_a")
    second = _make_account("acc_model_b")
    repo = _StubAccountsRepository()

    async def fake_ensure_fresh(self, account: Account, *, force: bool = False) -> Account:
        return account

    async def fake_fetch_models(access_token: str, account_id: str | None) -> list[UpstreamModel]:
        del access_token
        if account_id == first.chatgpt_account_id:
            raise scheduler_module.ModelFetchError(401, "Unauthorized")
        return [_make_model("gpt-5.1")]

    monkeypatch.setattr(scheduler_module.AuthManager, "ensure_fresh", fake_ensure_fresh)
    monkeypatch.setattr(scheduler_module, "fetch_models_for_plan", fake_fetch_models)

    models = await scheduler_module._fetch_with_failover([first, second], TokenEncryptor(), repo)

    assert models is not None
    assert [model.slug for model in models] == ["gpt-5.1"]
    assert repo.status_updates == [
        {
            "account_id": first.id,
            "status": AccountStatus.PAUSED,
            "deactivation_reason": PAUSE_REASON_MODEL_REFRESH,
            "reset_at": None,
        }
    ]
    assert first.status == AccountStatus.PAUSED


@pytest.mark.asyncio
async def test_fetch_with_failover_returns_none_when_only_candidate_hits_401(monkeypatch) -> None:
    account = _make_account("acc_model_only")
    repo = _StubAccountsRepository()

    async def fake_ensure_fresh(self, account: Account, *, force: bool = False) -> Account:
        return account

    async def fake_fetch_models(access_token: str, account_id: str | None) -> list[UpstreamModel]:
        del access_token, account_id
        raise scheduler_module.ModelFetchError(401, "Unauthorized")

    monkeypatch.setattr(scheduler_module.AuthManager, "ensure_fresh", fake_ensure_fresh)
    monkeypatch.setattr(scheduler_module, "fetch_models_for_plan", fake_fetch_models)

    models = await scheduler_module._fetch_with_failover([account], TokenEncryptor(), repo)

    assert models is None
    assert repo.status_updates[-1]["account_id"] == account.id
    assert repo.status_updates[-1]["status"] == AccountStatus.PAUSED
    assert repo.status_updates[-1]["deactivation_reason"] == PAUSE_REASON_MODEL_REFRESH
class _StubAuthManager:
    def __init__(self, _repo: object) -> None:
        pass

    async def ensure_fresh(self, account: Account, *, force: bool = False) -> Account:
        return account


@pytest.mark.asyncio
async def test_fetch_models_for_plan_marks_transport_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    session = MagicMock()
    session.get.side_effect = aiohttp.ClientError("dns failed")

    monkeypatch.setattr(
        model_fetcher_module,
        "get_codex_version_cache",
        lambda: SimpleNamespace(get_version=AsyncMock(return_value="1.2.3")),
    )

    @contextlib.asynccontextmanager
    async def lease_session():
        yield session

    monkeypatch.setattr(model_fetcher_module, "lease_http_session", lease_session)
    monkeypatch.setattr(
        model_fetcher_module,
        "get_settings",
        lambda: SimpleNamespace(upstream_base_url="https://example.test/backend-api"),
    )

    with pytest.raises(model_fetcher_module.ModelFetchError) as excinfo:
        await model_fetcher_module.fetch_models_for_plan("access-token", "account-1")

    exc = excinfo.value
    assert exc.status_code == 0
    assert exc.transport_error is True
    assert "dns failed" in exc.message


@pytest.mark.asyncio
async def test_refresh_access_token_marks_transport_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    session = MagicMock()
    session.post.side_effect = aiohttp.ClientError("dns failed")

    monkeypatch.setattr(
        refresh_module,
        "get_settings",
        lambda: SimpleNamespace(
            auth_base_url="https://auth.example.test",
            oauth_client_id="client-id",
            oauth_scope="openid profile",
            token_refresh_timeout_seconds=15.0,
        ),
    )

    with pytest.raises(refresh_module.RefreshError) as excinfo:
        await refresh_module.refresh_access_token("refresh-token", session=session)

    exc = excinfo.value
    assert exc.code == "transport_error"
    assert exc.is_permanent is False
    assert exc.transport_error is True
    assert "dns failed" in exc.message


@pytest.mark.asyncio
async def test_fetch_with_failover_refreshes_http_client_after_transport_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account = _account()
    encryptor = MagicMock()
    encryptor.decrypt.return_value = "access-token"
    expected_models = [_model("gpt-5.4")]

    fetch_models_for_plan = AsyncMock(
        side_effect=[
            scheduler_module.ModelFetchError(0, "temporary dns failure", transport_error=True),
            expected_models,
        ]
    )
    refresh_http_client = AsyncMock()

    monkeypatch.setattr(scheduler_module, "AuthManager", _StubAuthManager)
    monkeypatch.setattr(scheduler_module, "fetch_models_for_plan", fetch_models_for_plan)
    monkeypatch.setattr(scheduler_module, "refresh_http_client", refresh_http_client)

    result = await scheduler_module._fetch_with_failover([account], encryptor, MagicMock())

    assert result == expected_models
    refresh_http_client.assert_awaited_once()
    assert fetch_models_for_plan.await_count == 2
    assert encryptor.decrypt.call_count == 2


@pytest.mark.asyncio
async def test_fetch_with_failover_refreshes_http_client_after_token_refresh_transport_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account = _account()
    encryptor = MagicMock()
    encryptor.decrypt.return_value = "access-token"
    expected_models = [_model("gpt-5.4")]
    ensure_fresh_calls = 0

    class TransportFailingAuthManager:
        def __init__(self, _repo: object) -> None:
            pass

        async def ensure_fresh(self, account: Account, *, force: bool = False) -> Account:
            nonlocal ensure_fresh_calls
            ensure_fresh_calls += 1
            if ensure_fresh_calls == 1:
                raise scheduler_module.RefreshError(
                    "transport_error",
                    "Transport error during token refresh: dns failed",
                    False,
                    transport_error=True,
                )
            return account

    fetch_models_for_plan = AsyncMock(return_value=expected_models)
    refresh_http_client = AsyncMock()

    monkeypatch.setattr(scheduler_module, "AuthManager", TransportFailingAuthManager)
    monkeypatch.setattr(scheduler_module, "fetch_models_for_plan", fetch_models_for_plan)
    monkeypatch.setattr(scheduler_module, "refresh_http_client", refresh_http_client)

    result = await scheduler_module._fetch_with_failover([account], encryptor, MagicMock())

    assert result == expected_models
    refresh_http_client.assert_awaited_once()
    assert ensure_fresh_calls == 2
    fetch_models_for_plan.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetch_with_failover_attempts_transport_recovery_once_when_retry_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    accounts = [_account("account-1"), _account("account-2")]
    encryptor = MagicMock()
    encryptor.decrypt.return_value = "access-token"

    fetch_models_for_plan = AsyncMock(
        side_effect=[
            scheduler_module.ModelFetchError(0, "temporary dns failure", transport_error=True),
            scheduler_module.ModelFetchError(0, "temporary dns failure", transport_error=True),
            scheduler_module.ModelFetchError(0, "temporary dns failure", transport_error=True),
        ]
    )
    refresh_http_client = AsyncMock()

    monkeypatch.setattr(scheduler_module, "AuthManager", _StubAuthManager)
    monkeypatch.setattr(scheduler_module, "fetch_models_for_plan", fetch_models_for_plan)
    monkeypatch.setattr(scheduler_module, "refresh_http_client", refresh_http_client)

    result = await scheduler_module._fetch_with_failover(accounts, encryptor, MagicMock())

    assert result is None
    refresh_http_client.assert_awaited_once()
    assert fetch_models_for_plan.await_count == 3
    assert encryptor.decrypt.call_count == 3
