"""preserve request_logs when accounts are deleted

Revision ID: 20260415_000000_preserve_request_logs_on_account_delete
Revises: 20260413_000000_add_accounts_blocked_at
Create Date: 2026-04-15
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

revision = "20260415_000000_preserve_request_logs_on_account_delete"
down_revision = "20260413_000000_add_accounts_blocked_at"
branch_labels = None
depends_on = None

_REQUEST_LOGS_ACCOUNT_FK = "fk_request_logs_account_id_accounts"
_SQLITE_NAMING_CONVENTION = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def _table_exists(connection: Connection, table_name: str) -> bool:
    inspector = sa.inspect(connection)
    return inspector.has_table(table_name)


def _find_request_logs_account_fk(connection: Connection) -> dict[str, object] | None:
    inspector = sa.inspect(connection)
    if not inspector.has_table("request_logs"):
        return None
    for foreign_key in inspector.get_foreign_keys("request_logs"):
        constrained = foreign_key.get("constrained_columns") or []
        if list(constrained) != ["account_id"]:
            continue
        if foreign_key.get("referred_table") != "accounts":
            continue
        return foreign_key
    return None


def _normalized_ondelete(foreign_key: dict[str, object] | None) -> str | None:
    if foreign_key is None:
        return None
    options = foreign_key.get("options") or {}
    if not isinstance(options, dict):
        return None
    ondelete = options.get("ondelete")
    if ondelete is None:
        return None
    return str(ondelete).upper()


def _replace_sqlite_request_logs_account_fk(*, ondelete: str) -> None:
    with op.batch_alter_table("request_logs", naming_convention=_SQLITE_NAMING_CONVENTION) as batch_op:
        batch_op.drop_constraint(_REQUEST_LOGS_ACCOUNT_FK, type_="foreignkey")
        batch_op.create_foreign_key(
            _REQUEST_LOGS_ACCOUNT_FK,
            "accounts",
            ["account_id"],
            ["id"],
            ondelete=ondelete,
        )


def upgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(bind, "request_logs"):
        return

    foreign_key = _find_request_logs_account_fk(bind)
    if foreign_key is None or _normalized_ondelete(foreign_key) == "SET NULL":
        return

    if bind.dialect.name == "sqlite":
        _replace_sqlite_request_logs_account_fk(ondelete="SET NULL")
        return

    constraint_name = foreign_key.get("name")
    if constraint_name:
        op.drop_constraint(str(constraint_name), "request_logs", type_="foreignkey")
    op.create_foreign_key(
        _REQUEST_LOGS_ACCOUNT_FK,
        "request_logs",
        "accounts",
        ["account_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(bind, "request_logs"):
        return

    foreign_key = _find_request_logs_account_fk(bind)
    if foreign_key is None or _normalized_ondelete(foreign_key) == "CASCADE":
        return

    if bind.dialect.name == "sqlite":
        _replace_sqlite_request_logs_account_fk(ondelete="CASCADE")
        return

    constraint_name = foreign_key.get("name")
    if constraint_name:
        op.drop_constraint(str(constraint_name), "request_logs", type_="foreignkey")
    op.create_foreign_key(
        _REQUEST_LOGS_ACCOUNT_FK,
        "request_logs",
        "accounts",
        ["account_id"],
        ["id"],
        ondelete="CASCADE",
    )
