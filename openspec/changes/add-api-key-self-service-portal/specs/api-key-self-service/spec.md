## ADDED Requirements

### Requirement: Viewer login with LB API key

The system SHALL provide a separate viewer authentication surface where a user logs in with an existing LB API key (`sk-clb-*`). On successful validation, the system MUST issue a dedicated viewer session cookie scoped to the authenticated `api_key_id`.

#### Scenario: Valid viewer login

- **WHEN** a user submits `POST /api/viewer-auth/login` with a valid active, non-expired LB API key
- **THEN** the system issues the `codex_lb_viewer_session` cookie and returns an authenticated viewer session payload for that key

#### Scenario: Invalid viewer login

- **WHEN** a user submits `POST /api/viewer-auth/login` with a missing, inactive, invalid, or expired API key
- **THEN** the system returns 401 and does not create a viewer session

### Requirement: Viewer-scoped data isolation

All viewer routes SHALL derive scope from the authenticated viewer session and MUST only expose data for that session's `api_key_id`. Viewer responses MUST NOT expose internal LB account identifiers or other API keys.

#### Scenario: Viewer metadata is isolated to the logged-in key

- **WHEN** a viewer calls `GET /api/viewer/api-key`
- **THEN** the response contains only metadata for the authenticated key and does not expose any other key rows

#### Scenario: Viewer request logs are filtered by the logged-in key

- **WHEN** a viewer calls `GET /api/viewer/request-logs`
- **THEN** the response contains only request logs recorded with the authenticated `api_key_id`
- **AND** each row omits internal LB `account_id` data

### Requirement: Masked key visibility

The viewer portal SHALL expose only masked key content during normal browsing. The raw API key value MUST be shown exactly once during regeneration and MUST NOT be returned by normal viewer session or metadata endpoints.

#### Scenario: Viewer metadata is masked

- **WHEN** a viewer fetches session state or key metadata
- **THEN** the response includes `keyPrefix` and a masked display string, but no raw `key`

#### Scenario: Regeneration reveals the new raw key once

- **WHEN** a viewer calls `POST /api/viewer/api-key/regenerate`
- **THEN** the response includes the new raw key exactly once together with updated metadata

### Requirement: Regeneration keeps the viewer portal authenticated

When the authenticated viewer regenerates their own key, the old key MUST stop authenticating immediately and the viewer portal MUST remain authenticated by rotating its viewer session to the regenerated key identity in the same flow.

#### Scenario: Self-regenerate rotates session

- **WHEN** a viewer regenerates the key they are logged in with
- **THEN** the old key is rejected for future proxy/viewer logins
- **AND** the viewer session cookie is re-issued so the current portal session stays authenticated without a manual re-login
