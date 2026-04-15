## ADDED Requirements

### Requirement: Request-log foreign keys preserve history on account deletion

The database schema MUST preserve `request_logs` rows when an account is deleted. The `request_logs.account_id` foreign key MUST set the column to `NULL` instead of deleting the log row.

#### Scenario: Account deletion nulls linked request logs

- **GIVEN** `request_logs.account_id` references an existing account row
- **WHEN** that account row is deleted
- **THEN** the `request_logs` row remains present
- **AND** `request_logs.account_id` becomes `NULL`

#### Scenario: Fresh schema matches retention-safe foreign key behavior

- **WHEN** a fresh database is migrated to Alembic `head`
- **THEN** `request_logs.account_id` is nullable
- **AND** its foreign key behavior preserves the log row by setting `account_id` to `NULL` on account deletion
