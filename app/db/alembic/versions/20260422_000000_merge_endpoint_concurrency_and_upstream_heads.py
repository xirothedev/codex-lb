"""merge endpoint concurrency and upstream heads

Revision ID: 20260422_000000_merge_endpoint_concurrency_and_upstream_heads
Revises: 20260421_000000_add_proxy_endpoint_concurrency_limits,
20260421_120000_merge_request_log_lookup_and_plan_type_heads
Create Date: 2026-04-22
"""

from __future__ import annotations

revision = "20260422_000000_merge_endpoint_concurrency_and_upstream_heads"
down_revision = (
    "20260421_000000_add_proxy_endpoint_concurrency_limits",
    "20260421_120000_merge_request_log_lookup_and_plan_type_heads",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    return


def downgrade() -> None:
    return
