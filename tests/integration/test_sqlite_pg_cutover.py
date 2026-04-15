from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import event, select
from sqlalchemy import create_engine as create_sync_engine
from sqlalchemy.orm import Session as SyncSession

from app.core.crypto import TokenEncryptor
from app.core.utils.time import utcnow
from app.db.models import (
    Account,
    AccountStatus,
    AdditionalUsageHistory,
    ApiFirewallAllowlist,
    ApiKey,
    ApiKeyAccountAssignment,
    ApiKeyLimit,
    AuditLog,
    Base,
    DashboardSettings,
    LimitType,
    LimitWindow,
    RateLimitAttempt,
    RequestLog,
    StickySession,
    StickySessionKind,
    UsageHistory,
)
from app.db.session import SessionLocal, engine as app_engine
from app.db.sqlite_pg_cutover import run_sqlite_to_postgres_sync

pytestmark = pytest.mark.integration


def _postgres_database_url() -> str | None:
    url = str(app_engine.url)
    if url.startswith("postgresql+"):
        return url
    return None


def _make_account(account_id: str, email: str) -> Account:
    encryptor = TokenEncryptor()
    return Account(
        id=account_id,
        email=email,
        plan_type="plus",
        access_token_encrypted=encryptor.encrypt("access"),
        refresh_token_encrypted=encryptor.encrypt("refresh"),
        id_token_encrypted=encryptor.encrypt("id"),
        last_refresh=utcnow(),
        status=AccountStatus.ACTIVE,
        deactivation_reason=None,
    )


@pytest.mark.asyncio
@pytest.mark.skipif(_postgres_database_url() is None, reason="requires PostgreSQL test database")
async def test_sqlite_to_postgres_full_copy_and_final_sync(db_setup, tmp_path: Path):
    del db_setup
    target_database_url = _postgres_database_url()
    assert target_database_url is not None

    source_path = tmp_path / "cutover-source.sqlite"
    source_url = f"sqlite:///{source_path}"
    source_engine = create_sync_engine(source_url, future=True)

    @event.listens_for(source_engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    try:
        Base.metadata.create_all(source_engine)

        created_at = datetime(2026, 4, 15, 0, 0, 0)
        with SyncSession(source_engine) as session:
            account = _make_account("acc_cutover", "cutover@example.com")
            api_key = ApiKey(
                id="key_cutover",
                name="cutover-key",
                key_hash="hash_cutover",
                key_prefix="sk-clb-cutover",
                allowed_models=None,
                expires_at=None,
                is_active=True,
            )
            limit = ApiKeyLimit(
                id=11,
                api_key_id=api_key.id,
                limit_type=LimitType.TOTAL_TOKENS,
                limit_window=LimitWindow.WEEKLY,
                max_value=1000,
                current_value=15,
                model_filter=None,
                reset_at=created_at,
            )
            session.add(DashboardSettings(id=1))
            session.add(account)
            session.add(api_key)
            session.add(limit)
            session.add(ApiKeyAccountAssignment(api_key_id=api_key.id, account_id=account.id))
            session.add(ApiFirewallAllowlist(ip_address="10.0.0.1"))
            session.add(
                RequestLog(
                    id=101,
                    account_id=account.id,
                    api_key_id=api_key.id,
                    request_id="req_full_1",
                    requested_at=created_at,
                    model="model-alpha",
                    input_tokens=12,
                    output_tokens=3,
                    status="success",
                )
            )
            session.add(
                UsageHistory(
                    id=201,
                    account_id=account.id,
                    recorded_at=created_at,
                    window="primary",
                    used_percent=0.2,
                )
            )
            session.add(
                AdditionalUsageHistory(
                    id=301,
                    account_id=account.id,
                    quota_key="codex_other",
                    limit_name="codex_other",
                    metered_feature="spark",
                    window="primary",
                    used_percent=0.1,
                    recorded_at=created_at,
                )
            )
            session.add(
                StickySession(
                    key="sticky_cutover",
                    kind=StickySessionKind.STICKY_THREAD,
                    account_id=account.id,
                )
            )
            session.add(AuditLog(id=401, action="cutover_seed", timestamp=created_at))
            session.add(RateLimitAttempt(id=501, key="limit-cutover", type="password", attempted_at=created_at))
            session.commit()

        full_result = run_sqlite_to_postgres_sync(
            source_sqlite=str(source_path),
            target_database_url=target_database_url,
            mode="full-copy",
            batch_size=50,
        )
        assert full_result.mode == "full-copy"

        async with SessionLocal() as session:
            assert (await session.execute(select(RequestLog))).scalars().all()[0].id == 101
            assert (await session.execute(select(UsageHistory))).scalars().all()[0].id == 201
            assert (await session.execute(select(ApiKeyLimit))).scalars().all()[0].id == 11

        with SyncSession(source_engine) as session:
            session.add(
                RequestLog(
                    id=102,
                    account_id="acc_cutover",
                    api_key_id="key_cutover",
                    request_id="req_final_2",
                    requested_at=datetime(2026, 4, 15, 0, 5, 0),
                    model="model-alpha",
                    input_tokens=20,
                    output_tokens=4,
                    status="success",
                )
            )
            session.add(AuditLog(id=402, action="cutover_final", timestamp=datetime(2026, 4, 15, 0, 5, 0)))
            session.add(
                RateLimitAttempt(
                    id=502,
                    key="limit-cutover-final",
                    type="password",
                    attempted_at=datetime(2026, 4, 15, 0, 5, 0),
                )
            )
            account = session.get(Account, "acc_cutover")
            assert account is not None
            session.delete(account)
            session.commit()

        final_result = run_sqlite_to_postgres_sync(
            source_sqlite=str(source_path),
            target_database_url=target_database_url,
            mode="final-sync",
            batch_size=50,
        )
        assert final_result.mode == "final-sync"

        async with SessionLocal() as session:
            logs = list((await session.execute(select(RequestLog).order_by(RequestLog.id.asc()))).scalars().all())
            assert [log.id for log in logs] == [101, 102]
            assert all(log.account_id is None for log in logs)

            accounts = list((await session.execute(select(Account))).scalars().all())
            assert accounts == []

            assert list((await session.execute(select(UsageHistory))).scalars().all()) == []
            assert list((await session.execute(select(AdditionalUsageHistory))).scalars().all()) == []
            assert list((await session.execute(select(StickySession))).scalars().all()) == []
            assert list((await session.execute(select(ApiKeyAccountAssignment))).scalars().all()) == []

            api_key = (await session.execute(select(ApiKey).where(ApiKey.id == "key_cutover"))).scalar_one()
            assert api_key is not None

            audit_ids = [
                row.id for row in (await session.execute(select(AuditLog).order_by(AuditLog.id.asc()))).scalars()
            ]
            assert audit_ids == [401, 402]

            attempt_ids = [
                row.id
                for row in (await session.execute(select(RateLimitAttempt).order_by(RateLimitAttempt.id.asc()))).scalars()
            ]
            assert attempt_ids == [501, 502]

            next_log = RequestLog(
                account_id=None,
                api_key_id="key_cutover",
                request_id="req_after_sync",
                requested_at=datetime(2026, 4, 15, 0, 10, 0),
                model="model-alpha",
                status="success",
            )
            session.add(next_log)
            await session.commit()
            assert next_log.id > 102
    finally:
        source_engine.dispose()
