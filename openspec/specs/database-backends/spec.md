# database-backends Specification

## Purpose

See context docs for background.

## Requirements

### Requirement: Helm external PostgreSQL wiring resolves a non-empty database URL

When the Helm chart deploys with `postgresql.enabled=false`, it MUST provide a non-empty `CODEX_LB_DATABASE_URL` to the workload from one of the supported external database inputs. The chart MUST accept a direct `externalDatabase.url`, and it MUST also support reading `database-url` from an operator-provided external database secret reference without requiring the application encryption-key secret to be the same object.

#### Scenario: Direct external database URL is used

- **WHEN** `postgresql.enabled=false`
- **AND** `externalDatabase.url` is non-empty
- **THEN** the rendered workload uses that value for `CODEX_LB_DATABASE_URL`

#### Scenario: External database URL comes from a dedicated secret reference

- **WHEN** `postgresql.enabled=false`
- **AND** `externalDatabase.existingSecret` is set
- **THEN** the rendered workload reads `database-url` from that secret for `CODEX_LB_DATABASE_URL`

#### Scenario: Default SQLite startup uses quick validation
- **GIVEN** the configured database URL is a SQLite file
- **AND** `CODEX_LB_DATABASE_SQLITE_STARTUP_CHECK_MODE` is unset
- **WHEN** the service starts
- **THEN** it runs `PRAGMA quick_check`
- **AND** it does not run `PRAGMA integrity_check`

#### Scenario: Full SQLite startup validation is explicitly enabled
- **GIVEN** the configured database URL is a SQLite file
- **AND** `CODEX_LB_DATABASE_SQLITE_STARTUP_CHECK_MODE=full`
- **WHEN** the service starts
- **THEN** it runs `PRAGMA integrity_check`

#### Scenario: SQLite startup validation can be skipped
- **GIVEN** the configured database URL is a SQLite file
- **AND** `CODEX_LB_DATABASE_SQLITE_STARTUP_CHECK_MODE=off`
- **WHEN** the service starts
- **THEN** it skips startup SQLite validation

### Requirement: Test suite supports backend selection
The test bootstrap MUST allow callers to override `CODEX_LB_DATABASE_URL` via environment and MUST default to SQLite when no override is provided.

#### Scenario: CI sets PostgreSQL URL
- **WHEN** CI sets `CODEX_LB_DATABASE_URL` to a PostgreSQL DSN
- **THEN** tests run against PostgreSQL without modifying test code

#### Scenario: Local test run without URL override
- **WHEN** tests are run without setting `CODEX_LB_DATABASE_URL`
- **THEN** tests run against a temporary SQLite database

### Requirement: CI validates both default and optional backends
CI MUST keep SQLite-backed tests as the default path and MUST run an additional PostgreSQL-backed test job.

#### Scenario: CI workflow execution
- **WHEN** CI runs on push or pull request
- **THEN** at least one pytest job runs with SQLite and another pytest job runs with PostgreSQL

### Requirement: ORM enums persist schema string values
ORM enum columns backed by named PostgreSQL enums MUST persist the lowercase string values defined by the schema and migrations, not Python enum member names.

#### Scenario: SQLAlchemy binds account and API key enums
- **WHEN** the ORM metadata is built for `Account.status`, `ApiKeyLimit.limit_type`, and `ApiKeyLimit.limit_window`
- **THEN** each SQLAlchemy enum type exposes the same lowercase string values used by migrations and persisted rows

### Requirement: SQLite-to-PostgreSQL cutover tooling is available
The project MUST provide an operator-invoked tool that copies durable codex-lb data from a SQLite database into a PostgreSQL database configured with the current schema.

The tool MUST support:

- an initial full copy into PostgreSQL
- a final sync pass that refreshes mutable state tables and appends newly created history rows

The tool MUST skip transient runtime tables whose contents can be rebuilt after restart.

#### Scenario: Initial full copy seeds PostgreSQL

- **WHEN** an operator runs the cutover tool in full-copy mode against a SQLite source and empty PostgreSQL target
- **THEN** durable codex-lb tables are copied into PostgreSQL
- **AND** preserved primary keys remain stable so later sync passes can append new history rows safely

#### Scenario: Final sync refreshes mutable state and appends history

- **GIVEN** PostgreSQL was already seeded by an earlier full copy
- **WHEN** an operator runs the cutover tool in final-sync mode during production cutover
- **THEN** mutable state tables are synchronized to the latest SQLite contents
- **AND** history tables append only rows created after the earlier full copy
- **AND** transient runtime tables remain excluded from the sync

