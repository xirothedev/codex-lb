"""merge upstream durable bridge and fork migration heads

Revision ID: 20260518_010000_merge_upstream_durable_bridge_and_fork_heads
Revises: 20260511_000000_merge_drop_endpoint_concurrency_and_upstream_heads,
20260518_000000_add_http_bridge_durable_input_prefix
Create Date: 2026-05-18 01:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "20260518_010000_merge_upstream_durable_bridge_and_fork_heads"
down_revision: str | Sequence[str] | None = (
    "20260511_000000_merge_drop_endpoint_concurrency_and_upstream_heads",
    "20260518_000000_add_http_bridge_durable_input_prefix",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
