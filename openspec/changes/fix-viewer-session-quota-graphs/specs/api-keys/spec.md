## ADDED Requirements

### Requirement: Viewer sessions are stateless and key-scoped

The viewer login API SHALL issue an HTTP-only cookie whose value contains an encrypted stateless viewer session with the authenticated API key id and an expiry timestamp. The encrypted session MUST NOT contain the raw API key.

#### Scenario: Viewer login survives process-local state reset
- **WHEN** a viewer logs in and receives a viewer session cookie
- **AND** process-local viewer session state is empty
- **THEN** viewer portal endpoints still authenticate the request using the encrypted cookie payload until the cookie expires

#### Scenario: Invalid viewer session is rejected
- **WHEN** a viewer request includes no cookie, an invalid cookie, or an expired cookie
- **THEN** the viewer portal returns `401`

### Requirement: Viewer authorization uses the live API key record

Viewer portal endpoints SHALL re-read the API key record identified by the viewer session before returning key-scoped data. If the key no longer exists or is inactive, the endpoint SHALL return `401`.

#### Scenario: Inactive key cannot keep using viewer portal
- **GIVEN** a viewer session was created for an API key
- **WHEN** that API key becomes inactive or deleted
- **THEN** subsequent viewer portal requests using the old session are rejected with `401`

### Requirement: Viewer exposes key-scoped 7-day usage graph data

The viewer portal SHALL expose authenticated API key usage graph endpoints under `/viewer` that return only data for the API key identified by the viewer session:

- `GET /viewer/trends` returns 7-day cost and token trend points.
- `GET /viewer/usage-7d` returns 7-day total usage and per-account cost breakdown.

#### Scenario: Viewer trend data is scoped to the session key
- **WHEN** a viewer requests `/viewer/trends`
- **THEN** the response includes only cost and token points for the authenticated API key

#### Scenario: Viewer account-cost data is scoped to the session key
- **WHEN** a viewer requests `/viewer/usage-7d`
- **THEN** the response includes only 7-day totals and account-cost buckets for the authenticated API key

