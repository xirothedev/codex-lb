## 1. Specs

- [x] 1.1 Add viewer privacy requirement for account-cost data.
- [x] 1.2 Add viewer request-log pagination requirements.

## 2. Backend

- [x] 2.1 Add page/page-size pagination metadata to `/viewer/logs`.
- [x] 2.2 Keep `/viewer/logs` scoped to the authenticated API key.
- [x] 2.3 Return no account-cost buckets from `/viewer/usage-7d`.

## 3. Frontend

- [x] 3.1 Add pagination controls for viewer request logs.
- [x] 3.2 Remove account-cost donut rendering from the viewer dashboard.
- [x] 3.3 Preserve viewer 7-day trend chart rendering.

## 4. Verification

- [x] 4.1 Add backend tests for pagination and account-cost privacy.
- [x] 4.2 Add frontend tests for pagination controls and account leak prevention.
- [x] 4.3 Run focused frontend/backend tests and `openspec validate --specs`.
