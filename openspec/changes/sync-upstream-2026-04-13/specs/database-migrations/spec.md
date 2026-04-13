## MODIFIED Requirements

### Requirement: Automatic SQLite pre-migration backup

The system SHALL create a SQLite backup before applying startup migrations when an upgrade is needed. For Docker-hosted single-instance production rollouts that use the container entrypoint migration path instead of the in-app startup path, operators MUST create an explicit SQLite snapshot before the live container is replaced.

#### Scenario: Startup detects pending migration on SQLite

- **GIVEN** the configured database is a SQLite file
- **AND** startup migration is enabled
- **AND** migration state indicates upgrade is required
- **WHEN** startup migration begins
- **THEN** the system creates a pre-migration backup file
- **AND** enforces configured retention on backup files

#### Scenario: Container-entrypoint rollout targets a live SQLite volume

- **GIVEN** a production rollout uses the Docker entrypoint path that runs `python -m app.db.migrate upgrade` before the application starts
- **AND** that path is not relying on the in-app startup migration hook
- **WHEN** operators prepare to replace the live container
- **THEN** they create an explicit restorable SQLite snapshot before the new container is allowed to migrate the live database
- **AND** they do not treat the old container image alone as a sufficient rollback mechanism after schema advancement
