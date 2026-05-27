## Why

The viewer dashboard currently exposes the dashboard account-cost breakdown in the viewer portal. That leaks account identity/usage details, such as account emails, to API-key viewers who should only see usage for their own key. The viewer request logs also load a fixed first page without pagination controls, so users cannot navigate larger log sets.

## What Changes

- Ensure viewer-only usage endpoints never expose account-level identity or cost buckets.
- Remove account-cost donut rendering from the viewer dashboard.
- Add page-based pagination to viewer request logs while keeping the existing key-scoped filtering.
- Add backend and frontend coverage for viewer log pagination and account-privacy behavior.

## Impact

- Public viewer endpoint behavior changes:
  - `/viewer/usage-7d` still returns 7-day totals for the authenticated API key, but `account_costs` is always empty.
  - `/viewer/logs` accepts `page` and `page_size` and returns pagination metadata.
- Dashboard APIs tab behavior is unchanged and may continue showing account-cost breakdowns to authenticated dashboard users.
