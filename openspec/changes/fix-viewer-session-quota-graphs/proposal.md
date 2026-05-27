## Why

The public web viewer currently loses its authenticated state on reload, shows cost quota limits as raw microdollar integers, and lacks the usage trend/account-cost visualization already available to dashboard users in the APIs tab. This makes customer-facing usage data misleading and hard to audit.

## What Changes

- Make viewer sessions stateless and cookie-backed so a valid viewer login survives frontend reloads and backend in-memory store resets.
- Validate viewer portal requests against the live API key record so inactive or deleted keys cannot keep using an old viewer cookie.
- Format viewer `cost_usd` quota limits as dollars while preserving token and credit limit formatting.
- Add viewer-only 7-day usage trend and account-cost endpoints for the authenticated API key.
- Reuse the APIs tab usage panel visual pattern in `/viewer`: account-cost donut, token/cost trend chart, and accumulated toggle.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `api-keys`: API-key self-service viewer sessions and viewer usage endpoints expose durable, key-scoped usage data without revealing raw API keys.
- `frontend-architecture`: The viewer page renders durable auth state, correct cost quota formatting, and dashboard-equivalent usage visualization.

## Impact

- Backend: `app/modules/viewer_auth/*`, `app/modules/viewer_portal/*`, API-key service reuse
- Frontend: `frontend/src/features/viewer/*`, reused APIs tab chart/donut components
- Tests: viewer auth/session tests, viewer portal endpoint tests, viewer component/store tests

