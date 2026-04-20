## 1. Specs

- [x] 1.1 Add API-key requirements for request-log and usage retention across account deletion.
- [x] 1.2 Add database-backend requirements for SQLite-to-PostgreSQL cutover tooling.
- [x] 1.3 Add database-migration requirements for retention-safe request-log foreign-key behavior.

## 2. Implementation

- [x] 2.1 Patch account deletion so it no longer deletes `request_logs`, and update ORM metadata to use `ON DELETE SET NULL` for `request_logs.account_id`.
- [x] 2.2 Add an Alembic revision that changes the `request_logs.account_id` foreign key from cascade-delete to set-null across supported backends.
- [x] 2.3 Add a SQLite-to-PostgreSQL sync tool for initial bulk copy and final cutover sync.
- [x] 2.4 Add change-level cutover notes for production VPS migration and rollback.

## 3. Tests

- [x] 3.1 Add regression coverage proving account deletion keeps request logs and API-key usage totals intact.
- [x] 3.2 Add migration coverage proving deleting an account nulls `request_logs.account_id` instead of deleting the log row.
- [x] 3.3 Add sync-tool coverage for full-copy and delta-sync behavior.
- [x] 3.4 Validate OpenSpec changes.
