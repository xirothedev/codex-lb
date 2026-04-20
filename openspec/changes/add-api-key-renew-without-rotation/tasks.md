## 1. OpenSpec delta

- [x] 1.1 Add `api-keys` spec delta for same-key renew semantics, reservation safety, and renewal audit behavior
- [x] 1.2 Add `frontend-architecture` spec delta for the dedicated renew action and lifetime-usage copy

## 2. Backend renew flow

- [x] 2.1 Add a service/repository guard that blocks `resetUsage` updates while the key has `reserved` or `settling` usage reservations
- [x] 2.2 Surface the new conflict as a typed API error and emit `api_key_renewed` audit logs for successful renewals
- [x] 2.3 Preserve existing same-key behavior: renewing updates limit counters and expiry without changing `api_key_id`, `key_hash`, or request-log aggregates

## 3. Frontend dashboard flow

- [x] 3.1 Add a dedicated renew action and dialog in the admin API key management UI
- [x] 3.2 Submit renew through the existing update mutation with `resetUsage: true` and the selected `expiresAt`
- [x] 3.3 Relabel the dashboard usage summary copy to clarify that it remains lifetime history after renew

## 4. Verification

- [x] 4.1 Add backend unit/integration coverage for successful renewals, reservation conflicts, and renewal audit logging
- [x] 4.2 Add frontend hook/integration coverage for the renew action and updated lifetime-usage copy
- [x] 4.3 Run targeted backend/frontend tests and `openspec validate --specs`
