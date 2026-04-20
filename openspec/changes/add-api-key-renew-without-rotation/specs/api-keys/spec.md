## MODIFIED Requirement: API Key update

The system SHALL allow updating key properties via `PATCH /api/api-keys/{id}`. Updatable fields: `name`, `allowedModels`, `weeklyTokenLimit`, `expiresAt`, `isActive`, account assignments, and explicit usage reset controls. The key hash and prefix MUST NOT be modifiable.

When `resetUsage` is requested, the system MUST reset the current quota counters for the key's active limit rows without changing the API key value or database identity. Request logs, usage summaries derived from `request_logs`, and trends tied to the same `api_key_id` MUST remain intact.

The system MUST reject a `resetUsage` update with a conflict response while the key still has in-flight usage reservations in `reserved` or `settling` state.

#### Scenario: Renew depleted key without rotating raw key

- **WHEN** admin submits `PATCH /api/api-keys/{id}` with `{ "resetUsage": true, "expiresAt": "2026-05-01T00:00:00Z" }`
- **THEN** the system resets each active limit row for that key to `current_value = 0` and advances `reset_at`
- **AND** the key keeps the same `id`, `keyPrefix`, and raw API key secret
- **AND** historical request logs and lifetime usage summaries for that `api_key_id` remain available

#### Scenario: Renew blocked while usage reservation is in flight

- **WHEN** admin submits `PATCH /api/api-keys/{id}` with `resetUsage = true`
- **AND** the key has at least one usage reservation in `reserved` or `settling` state
- **THEN** the system rejects the request with HTTP 409
- **AND** none of the key's limits or expiry fields are modified

### MODIFIED Requirement: Frontend API Key management

The SPA settings page SHALL include an API Key management section with a key actions menu containing edit, renew, regenerate, and delete actions. The renew flow MUST allow the admin to choose a new expiration date, reset current quota counters, keep the existing API key secret, and preserve lifetime usage history.

#### Scenario: Renew action preserves key identity

- **WHEN** admin confirms renew for an existing API key in the dashboard
- **THEN** the frontend submits an update request using the existing key id with `resetUsage: true` and the selected `expiresAt`
- **AND** the UI does not display a new raw API key dialog because the key value did not rotate

### ADDED Requirement: API key renewal audit trail

Successful API key renewals MUST write a dedicated audit log entry so operators can distinguish a renew from generic metadata edits or key rotation.

#### Scenario: Renewal writes audit record

- **WHEN** an admin successfully renews an API key
- **THEN** the system writes an `api_key_renewed` audit entry
- **AND** the audit details include the renewed `key_id` and the old/new expiry values
