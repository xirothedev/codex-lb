## 1. Specs

- [ ] 1.1 Add API-key requirements for request-log and usage retention across account deletion.
- [ ] 1.2 Add database-backend requirements for SQLite-to-PostgreSQL cutover tooling.
- [ ] 1.3 Add database-migration requirements for retention-safe request-log foreign-key behavior.

## 2. Implementation

- [ ] 2.1 Patch account deletion so it no longer deletes `request_logs`, and update ORM metadata to use `ON DELETE SET NULL` for `request_logs.account_id`.
- [ ] 2.2 Add an Alembic revision that changes the `request_logs.account_id` foreign key from cascade-delete to set-null across supported backends.
- [ ] 2.3 Add a SQLite-to-PostgreSQL sync tool for initial bulk copy and final cutover sync.
- [ ] 2.4 Add change-level cutover notes for production VPS migration and rollback.

## 3. Tests

- [ ] 3.1 Add regression coverage proving account deletion keeps request logs and API-key usage totals intact.
- [ ] 3.2 Add migration coverage proving deleting an account nulls `request_logs.account_id` instead of deleting the log row.
- [ ] 3.3 Add sync-tool coverage for full-copy and delta-sync behavior.
- [ ] 3.4 Validate OpenSpec changes.
