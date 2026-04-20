## Why

Operators can already edit an API key's expiry and explicitly reset usage counters, but there is no first-class renew workflow for extending a depleted key without rotating it. When a customer has exhausted quota or needs a renewal term extension, the dashboard should support renewing the existing key so proxy clients keep working and historical request logs remain attached to the same key identity.

## What Changes

- Add an admin renew flow for existing API keys that resets current quota counters and refreshes the expiry date without changing the raw API key value
- Guard renew/reset operations when the key still has in-flight usage reservations so quota counters cannot be reset mid-request
- Record a dedicated audit event for successful renewals
- Add a dedicated dashboard renew action and confirmation dialog that clearly distinguishes lifetime usage history from current quota counters

## Capabilities

### New Capabilities

### Modified Capabilities

- `api-keys`: API key lifecycle requirements gain an explicit renew flow, reservation-safety guard, and renewal audit semantics
- `frontend-architecture`: the dashboard API key management UI gains a dedicated renew action and lifetime-usage copy

## Impact

- Code: `app/modules/api_keys/*`, `app/db/models.py`, `frontend/src/features/api-keys/*`
- Tests: `tests/unit/test_api_keys_service.py`, `tests/integration/test_api_keys_api.py`, `frontend/src/features/api-keys/hooks/use-api-keys.test.ts`, `frontend/src/__integration__/apis-page-flow.test.tsx`
- Specs: change deltas for `api-keys` and `frontend-architecture`
