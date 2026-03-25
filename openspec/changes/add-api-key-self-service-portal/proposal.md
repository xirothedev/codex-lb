## Why

The dashboard currently only supports admin authentication via password/TOTP and exposes API key management as an admin-only settings feature. Operators need a self-service surface where an end user can log in with their own `sk-clb-*` API key and only see data for that key without exposing admin settings, internal LB account identifiers, or other users' keys.

## What Changes

- Add a separate `/viewer` self-service portal with API-key login and a dedicated viewer session cookie
- Add viewer-scoped backend endpoints for session state, masked API key metadata, request logs, and API key regeneration
- Filter all viewer data strictly by the authenticated `api_key_id` and hide internal account identifiers from viewer responses
- Reuse shared frontend layout, stats, dialog, and request-log table/filter primitives while keeping admin routes and behavior unchanged

## Impact

- Code: `app/core/auth/dependencies.py`, `app/dependencies.py`, `app/main.py`, new `app/modules/viewer_auth/*`, new `app/modules/viewer_portal/*`
- Code: `frontend/src/App.tsx`, `frontend/src/lib/api-client.ts`, new `frontend/src/features/viewer*/*`, shared request-log/header components
- Tests: backend viewer auth/request-log coverage plus frontend viewer portal/MSW coverage and admin regression coverage
- Specs: `openspec/specs/api-keys/spec.md`, `openspec/specs/frontend-architecture/spec.md`, new `openspec/specs/api-key-self-service/spec.md`
