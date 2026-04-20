## Context

API key quota enforcement is tracked on `api_key_limits`, while usage summaries and analytics are derived from `request_logs.api_key_id`. This means a same-key renewal can safely reset live quota counters without deleting historical logs, but only if the raw key, key hash, and primary key stay unchanged. The risky edge is `api_key_usage_reservations`: in-flight requests reserve quota against specific `limit_id` and `expected_reset_at` values, so resetting limits while reservations remain open can cause stale settlement writes or silently dropped quota adjustments.

## Goals / Non-Goals

**Goals:**
- Let admins renew a key by resetting current quota counters and updating `expiresAt` without rotating the key
- Keep request logs, lifetime usage aggregates, and viewer/admin identity references attached to the same `api_key_id`
- Block renew/reset while there are in-flight reservations for that key
- Expose a clear renew action in the admin dashboard without overloading regenerate semantics

**Non-Goals:**
- Viewer self-service renewal
- Deleting or rebasing historical request logs after renew
- Reworking generic edit semantics beyond what is needed for renew

## Decisions

### Reuse `PATCH /api/api-keys/{id}` for renew

The API already supports `resetUsage` and `expiresAt`, so renew remains a constrained PATCH flow instead of adding a separate backend endpoint. The admin UI will formalize renew by sending both fields together from a dedicated dialog.

### Reject renew/reset when reservations are in flight

Renew safety is enforced in `ApiKeysService.update_key()` before limit rows are rebuilt. The repository will count reservations for the key whose status is `reserved` or `settling`; if any exist, the service raises a domain error that maps to HTTP 409. This keeps quota counters and post-request settlement logic coherent without adding background reconciliation.

### Keep lifetime usage visible and relabel it

Because lifetime usage is sourced from `request_logs`, renew must not alter those aggregates. The dashboard will keep showing them, but the table label/copy will explicitly say `Usage (lifetime)` so operators do not mistake it for current-window quota counters.

### Add a dedicated renewal audit action

Renew should not be indistinguishable from a generic PATCH. The API route will emit `api_key_renewed` with old/new expiry and a reset flag when the renew flow succeeds.

## Risks / Trade-offs

- In-flight requests block renew more often than operators expect -> show a specific conflict error so they can retry later
- Generic PATCH still allows `resetUsage` without `expiresAt` -> keep backend compatibility, but make the dashboard renew flow always submit both fields
- Lifetime usage remaining visible after renew may surprise operators -> relabel usage and keep current-window counters in the Limit column
