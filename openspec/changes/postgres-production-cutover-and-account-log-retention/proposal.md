## Why

Production currently runs against SQLite, but the repo already supports PostgreSQL and validates it in CI. What is missing is an operator-safe cutover path from a live SQLite database to PostgreSQL on the VPS.

At the same time, deleting an account currently deletes `request_logs`, which breaks the requirement that API-key usage history and request-log history must survive account cleanup.

## What Changes

- Preserve `request_logs` when an account is deleted by nulling `request_logs.account_id` instead of cascading log deletion.
- Keep API-key usage summaries stable after account deletion because they continue to aggregate from `request_logs.api_key_id`.
- Add a one-time SQLite-to-PostgreSQL cutover tool that supports an initial full copy plus a final sync pass for production cutover.
- Capture the production cutover workflow in the change context so the VPS migration path is explicit and repeatable.

## Capabilities

### Modified Capabilities

- `api-keys`
- `database-backends`
- `database-migrations`
