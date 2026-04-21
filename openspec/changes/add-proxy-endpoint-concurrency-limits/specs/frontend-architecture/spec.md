## MODIFIED Requirements

### Requirement: Settings page

The Settings page SHALL include sections for: routing settings (sticky threads, reset priority, prompt-cache affinity TTL, and proxy endpoint concurrency limits), password management (setup/change/remove), TOTP management (setup/disable), API key auth toggle, API key management (table, create, edit, delete, regenerate), and sticky-session administration.

#### Scenario: Save routing settings

- **WHEN** a user toggles sticky threads, reset priority, updates the prompt-cache affinity TTL, or edits proxy endpoint concurrency limits
- **THEN** the app calls `PUT /api/settings` with the updated values

#### Scenario: View sticky-session mappings

- **WHEN** a user opens the sticky-session section on the Settings page
- **THEN** the app fetches sticky-session entries and displays each mapping's kind, account, timestamps, and stale/expiry state

#### Scenario: Purge stale prompt-cache mappings

- **WHEN** a user requests a stale purge from the sticky-session section
- **THEN** the app calls the sticky-session purge API and refreshes the list afterward

#### Scenario: Password setup

- **WHEN** a user sets a password from the settings page
- **THEN** the app calls `POST /api/dashboard-auth/password/setup` and reflects the new auth state

#### Scenario: API key management

- **WHEN** a user creates an API key via the settings page
- **THEN** the app calls `POST /api/api-keys` and displays the plain key in a dialog with a copy button and a warning that it will not be shown again
