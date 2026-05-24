"""drop proxy endpoint concurrency limits from dashboard settings

Revision ID: 20260424_000000_drop_proxy_endpoint_concurrency_limits
Revises: 20260422_000000_merge_endpoint_concurrency_and_upstream_heads
Create Date: 2026-04-24
"""

from __future__ import annotations

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

revision = "20260424_000000_drop_proxy_endpoint_concurrency_limits"
down_revision = "20260422_000000_merge_endpoint_concurrency_and_upstream_heads"
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
    if not columns or "proxy_endpoint_concurrency_limits" not in columns:
        return

    with op.batch_alter_table("dashboard_settings") as batch_op:
        batch_op.drop_column("proxy_endpoint_concurrency_limits")


def downgrade() -> None:
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
