# database-backends Specification

## Purpose

Define supported database backend wiring so local, Helm, SQLite, and external PostgreSQL deployments behave consistently.
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

### Requirement: PostgreSQL engines validate and recycle pooled connections

When `database_url` resolves to a PostgreSQL backend, the application MUST configure each async engine — both the request-path `engine` and the optional background-task `_background_engine` — with `pool_pre_ping=True` and a finite `pool_recycle` window. This is required so the application detects connections that the PostgreSQL server has silently closed (idle timeout, restart, network reset) before the first real query is dispatched on them, and so connections are cycled before they reach any reasonable upstream keep-alive boundary.

#### Scenario: Stale connections are rejected before checkout

- **WHEN** a pooled connection has been closed by the server while sitting idle
- **AND** that connection is the next one a session tries to use
- **THEN** SQLAlchemy issues a pre-ping (`SELECT 1`), detects the dead connection, and transparently replaces it
- **AND** the application returns `200` (or the real business-level result), not `500 server_error` with `asyncpg.InterfaceError: connection is closed`

#### Scenario: Pool recycle bounds connection age

- **WHEN** a pooled connection has been open longer than `database_pool_recycle_seconds`
- **AND** that connection is the next one a session tries to use
- **THEN** SQLAlchemy discards and replaces the connection before the next query
- **AND** the default `database_pool_recycle_seconds` is `1800` seconds

#### Scenario: SQLite backends are not affected

- **WHEN** `database_url` resolves to a SQLite backend (file or `:memory:`)
- **THEN** neither `pool_pre_ping` nor `pool_recycle` is configured on the engine
- **AND** existing SQLite-specific tuning (PRAGMAs, `busy_timeout`) is unchanged

### Requirement: Database pool controls cover request-adjacent background sessions
The service SHALL expose database pool settings for both the main request pool
and the background/request-adjacent session pool. The background pool SHALL
default to the main pool size and overflow settings, and operators MAY override
the background pool size and overflow separately.

#### Scenario: Background pool inherits main pool capacity
- **WHEN** `database_background_pool_size` and `database_background_max_overflow` are unset
- **THEN** the background/request-adjacent DB pool uses `database_pool_size` and `database_max_overflow`

#### Scenario: Background pool has explicit lower capacity
- **WHEN** `database_background_pool_size` and `database_background_max_overflow` are configured
- **THEN** the background/request-adjacent DB pool uses those explicit values
