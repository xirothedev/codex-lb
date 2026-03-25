from __future__ import annotations

from datetime import datetime, timezone

import pytest

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


def _make_model(slug: str) -> UpstreamModel:
    return UpstreamModel(
        slug=slug,
        display_name=slug,
        description=slug,
        context_window=128000,
        input_modalities=("text",),
        supported_reasoning_levels=(ReasoningLevel(effort="medium", description="default"),),
        default_reasoning_level="medium",
        supports_reasoning_summaries=False,
        support_verbosity=False,
        default_verbosity=None,
        prefer_websockets=False,
        supports_parallel_tool_calls=True,
        supported_in_api=True,
        minimal_client_version=None,
        priority=0,
        available_in_plans=frozenset({"plus"}),
        raw={},
    )


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
