"""merge drop_proxy_endpoint_concurrency_limits and dashboard_session_ttl heads

Revision ID: 20260511_000000_merge_drop_endpoint_concurrency_and_upstream_heads
Revises: 20260424_000000_drop_proxy_endpoint_concurrency_limits,
20260424_000000_merge_dashboard_session_ttl_and_request_log_heads
Create Date: 2026-05-11
"""

from __future__ import annotations

revision = "20260511_000000_merge_drop_endpoint_concurrency_and_upstream_heads"
down_revision = (
    "20260424_000000_drop_proxy_endpoint_concurrency_limits",
    "20260424_000000_merge_dashboard_session_ttl_and_request_log_heads",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
