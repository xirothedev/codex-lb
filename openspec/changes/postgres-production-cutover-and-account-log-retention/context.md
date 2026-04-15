## Overview

This change keeps source-code impact narrow:

- preserve request logs on account deletion
- keep API-key usage derived from request logs unchanged
- add a one-time cutover tool instead of changing normal runtime write paths

## Production Cutover Notes

1. Provision PostgreSQL on the VPS and run `python -m app.db.migrate upgrade` against it before copying data.
2. Run the sync tool in full-copy mode while SQLite-backed production is still serving traffic.
3. Start a candidate codex-lb instance against PostgreSQL on non-public ports and verify health.
4. Start drain on the SQLite-backed instance, wait for in-flight HTTP work and bridge sessions to settle, then run the tool in final-sync mode.
5. Flip the reverse proxy to the PostgreSQL-backed instance.
6. Keep the pre-cutover SQLite snapshot and previous app instance as rollback inventory until smoke checks pass.

## Table Classes

- Durable and copied: `accounts`, `dashboard_settings`, `api_keys`, `api_key_limits`, `api_key_accounts`, `request_logs`, `usage_history`, `additional_usage_history`, `audit_logs`, `rate_limit_attempts`, `sticky_sessions`, `api_firewall_allowlist`
- Transient and skipped: `scheduler_leader`, `cache_invalidation`, `bridge_ring_members`, `api_key_usage_reservations`, `api_key_usage_reservation_items`, `http_bridge_sessions`, `http_bridge_session_aliases`
