## ADDED Requirements

### Requirement: Single-host SQLite deployments create an explicit pre-cutover snapshot

When codex-lb is deployed from a Docker image on a single host against a SQLite database volume, the rollout workflow MUST create an explicit SQLite snapshot before the live container is replaced if the candidate image can apply new Alembic revisions.

#### Scenario: Live deployment introduces new Alembic revisions

- **GIVEN** the currently deployed container runs against a SQLite database volume
- **AND** the candidate image contains Alembic revisions beyond the live database head
- **WHEN** operators prepare a live rollout
- **THEN** they create a restorable SQLite snapshot before the candidate image is allowed to advance the live schema
- **AND** the rollback plan treats that snapshot as required state, not just the old container image

### Requirement: Candidate image is verified before live port takeover

The rollout workflow MUST verify that the candidate image can start successfully before it is allowed to claim the live loopback ports.

#### Scenario: Candidate image is prepared for promotion

- **GIVEN** the candidate image has been built successfully from the validated `master` head
- **AND** the production host uses fixed loopback bindings for the live codex-lb container
- **WHEN** operators stage the candidate on alternate loopback ports against a pre-cutover SQLite snapshot
- **THEN** the candidate container starts successfully
- **AND** the candidate reports the expected Alembic revision
- **AND** the candidate health check succeeds before the live container is stopped

### Requirement: Live cutover preserves rollback inventory

The rollout workflow MUST preserve both the previous container and the pre-cutover SQLite snapshot until the new live container has been verified.

#### Scenario: Live container is replaced

- **GIVEN** a verified candidate image is ready for production promotion
- **WHEN** operators replace the live codex-lb container on the production loopback ports
- **THEN** the previous container is renamed and retained for rollback
- **AND** the pre-cutover SQLite snapshot remains available after the new container starts
- **AND** operators verify the new image tag, live Alembic revision, and HTTP health before considering the rollout complete
