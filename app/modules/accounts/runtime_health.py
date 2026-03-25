from __future__ import annotations

from typing import Protocol

from app.db.models import Account, AccountStatus

PAUSE_REASON_PROXY_TRAFFIC = "Auto-paused after upstream 401 during proxy traffic"
PAUSE_REASON_USAGE_REFRESH = "Auto-paused after upstream 401 during usage refresh"
PAUSE_REASON_MODEL_REFRESH = "Auto-paused after upstream 401 during model refresh"


class AccountStatusWriter(Protocol):
    async def update_status(
        self,
        account_id: str,
        status: AccountStatus,
        deactivation_reason: str | None = None,
        reset_at: int | None = None,
    ) -> bool: ...


async def pause_account(
    repo: AccountStatusWriter,
    account: Account,
    reason: str,
) -> bool:
    updated = await repo.update_status(account.id, AccountStatus.PAUSED, reason, None)
    if updated:
        account.status = AccountStatus.PAUSED
        account.deactivation_reason = reason
        account.reset_at = None
    return updated
