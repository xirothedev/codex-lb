"""add proxy endpoint concurrency limits to dashboard settings

Revision ID: 20260421_000000_add_proxy_endpoint_concurrency_limits
Revises: 20260415_000000_preserve_request_logs_on_account_delete
Create Date: 2026-04-21
"""

from __future__ import annotations

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

revision = "20260421_000000_add_proxy_endpoint_concurrency_limits"
down_revision = "20260415_000000_preserve_request_logs_on_account_delete"
branch_labels = None
depends_on = None

_DEFAULT_LIMITS = {
    "responses": 0,
    "responses_compact": 0,
    "chat_completions": 0,
    "transcriptions": 0,
    "models": 0,
    "usage": 0,
}
_DEFAULT_LIMITS_JSON = json.dumps(_DEFAULT_LIMITS, separators=(",", ":"))


def _columns(connection: Connection, table_name: str) -> set[str]:
    inspector = sa.inspect(connection)
    if not inspector.has_table(table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    columns = _columns(bind, "dashboard_settings")
    if not columns or "proxy_endpoint_concurrency_limits" in columns:
        return

    with op.batch_alter_table("dashboard_settings") as batch_op:
        batch_op.add_column(
            sa.Column(
                "proxy_endpoint_concurrency_limits",
                sa.JSON(),
                nullable=False,
                server_default=sa.text(f"'{_DEFAULT_LIMITS_JSON}'"),
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    columns = _columns(bind, "dashboard_settings")
    if not columns or "proxy_endpoint_concurrency_limits" not in columns:
        return

    with op.batch_alter_table("dashboard_settings") as batch_op:
        batch_op.drop_column("proxy_endpoint_concurrency_limits")
