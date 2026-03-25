## 1. OpenSpec delta

- [x] 1.1 Add self-service viewer spec delta for API-key login, viewer-scoped responses, and one-time regeneration visibility
- [x] 1.2 Update API key and frontend architecture deltas to cover masked viewer metadata and the separate `/viewer` portal

## 2. Backend viewer scope

- [x] 2.1 Add viewer session models/store/service and viewer auth endpoints backed by API key validation
- [x] 2.2 Add viewer-scoped API key and request-log endpoints that filter strictly by the authenticated `api_key_id`
- [x] 2.3 Keep admin dashboard/session behavior unchanged and hide internal account identifiers from viewer responses

## 3. Frontend portal

- [x] 3.1 Add `/viewer` routes, viewer auth store, and API-key login form
- [x] 3.2 Build the viewer dashboard with shared layout/stats/request-log components and a one-time regenerate dialog
- [x] 3.3 Preserve existing admin routes and shared component behavior

## 4. Verification

- [x] 4.1 Add backend tests for viewer auth, viewer filtering, and regeneration/session rotation
- [x] 4.2 Add frontend/MSW tests for viewer login, portal rendering, and regenerate flow
- [x] 4.3 Run targeted backend/frontend tests and OpenSpec validation
