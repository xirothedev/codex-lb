"""merge accounts_alias and fork_compat heads

Revision ID: 20260524_000000_merge_accounts_alias_and_fork_compat
Revises: 20260513_000000_add_accounts_alias, 20260518_010000_merge_upstream_durable_bridge_and_fork_heads
Create Date: 2026-05-24
"""

from __future__ import annotations

revision = "20260524_000000_merge_accounts_alias_and_fork_compat"
down_revision = (
    "20260513_000000_add_accounts_alias",
    "20260518_010000_merge_upstream_durable_bridge_and_fork_heads",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
