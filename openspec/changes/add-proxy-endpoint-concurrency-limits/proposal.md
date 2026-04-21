## Why

The proxy currently has only coarse global admission controls (`backpressure` and `bulkhead`) plus a Responses-bridge queue that covers one internal path. Heavy proxy workloads can still starve each other, and operators cannot tune concurrency for specific API families without restarting the service.

## What Changes

- add family-based, per-replica concurrency limits for external proxy APIs
- expose those limits through dashboard settings so operators can adjust them without restart
- share counters across equivalent aliases and protocols for the same workload family
- fail fast with the existing proxy contracts instead of adding new request queues
- add logs and metrics for family-level concurrency rejections

## Capabilities

### New Capabilities
- `proxy-request-admission`: family-based proxy request admission control, settings exposure, and overload behavior for external proxy routes

### Modified Capabilities
- `frontend-architecture`: extend the Settings page routing controls to edit proxy endpoint concurrency limits
- `proxy-runtime-observability`: expose operator-visible logs and metrics for proxy endpoint concurrency rejections

## Impact

- changes request admission behavior for `/v1/*`, `/backend-api/codex/*`, `/backend-api/transcribe`, and `/api/codex/usage`
- adds a new dashboard settings field plus persistence/migration work for `dashboard_settings`
- touches proxy routing, settings API/schema/repository/service, frontend settings forms, and targeted proxy/frontend tests
