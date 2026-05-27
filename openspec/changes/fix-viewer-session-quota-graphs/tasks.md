## 1. Spec

- [x] 1.1 Add viewer session persistence and live key validation requirements.
- [x] 1.2 Add viewer usage graph and account-cost requirements.
- [x] 1.3 Add viewer cost quota formatting requirements.

## 2. Backend

- [x] 2.1 Replace viewer's process-local session store with a stateless encrypted-cookie session.
- [x] 2.2 Re-read the live API key for viewer portal authorization and reject inactive/deleted keys.
- [x] 2.3 Add `/viewer/trends` and `/viewer/usage-7d` endpoints using existing API-key usage aggregation.

## 3. Frontend

- [x] 3.1 Bootstrap viewer auth from the existing session before showing the login form.
- [x] 3.2 Render `cost_usd` quota limits in dollars.
- [x] 3.3 Reuse the APIs tab trend and account-cost donut UI in the viewer page.

## 4. Verification

- [x] 4.1 Add backend coverage for stateless viewer sessions, invalid sessions, inactive keys, and viewer usage endpoints.
- [x] 4.2 Add frontend coverage for viewer bootstrap, cost quota formatting, and graph rendering.
- [x] 4.3 Run focused frontend/backend tests and `openspec validate --specs`.
