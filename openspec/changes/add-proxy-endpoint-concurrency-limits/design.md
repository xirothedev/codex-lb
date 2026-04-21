## Context

The runtime already applies two coarse admission layers before requests reach route handlers:

- `BackpressureMiddleware` limits total concurrent HTTP/WebSocket work except `/health*`
- `BulkheadMiddleware` splits concurrency into proxy vs dashboard buckets by URL prefix

These controls are useful for whole-process protection, but they do not isolate one proxy workload family from another. Separately, the HTTP Responses bridge keeps its own session capacity and per-session queue limits inside `app/modules/proxy/service.py`, which protects only bridged Responses traffic and does not cover chat completions, transcriptions, model discovery, or usage reads.

This change adds a family-aware gate for external proxy routes only. Operators requested runtime editability, so the concurrency map needs to live in dashboard settings rather than env-only process settings.

## Goals / Non-Goals

**Goals:**
- enforce per-replica concurrency limits for external proxy endpoint families
- share one counter across equivalent aliases and protocols for the same workload
- keep overload behavior fail-fast and consistent with current proxy contracts
- let operators change limits through `GET/PUT /api/settings` without restart
- make rejections visible in logs and metrics

**Non-Goals:**
- cluster-wide distributed concurrency limits
- new request queues, leases, or token-bucket rate limiting
- extending the feature to dashboard, viewer, auth, or health routes
- changing existing bridge queue or bridge session capacity semantics

## Decisions

### 1. Use a fixed family map instead of arbitrary route keys

The limiter will expose one settings object with these fixed families:

- `responses`
- `responses_compact`
- `chat_completions`
- `transcriptions`
- `models`
- `usage`

These map to current external proxy routes as follows:

- `responses`: `POST /backend-api/codex/responses`, `POST /v1/responses`, `WEBSOCKET /backend-api/codex/responses`, `WEBSOCKET /v1/responses`
- `responses_compact`: `POST /backend-api/codex/responses/compact`, `POST /v1/responses/compact`
- `chat_completions`: `POST /v1/chat/completions`
- `transcriptions`: `POST /backend-api/transcribe`, `POST /v1/audio/transcriptions`
- `models`: `GET /backend-api/codex/models`, `GET /v1/models`
- `usage`: `GET /api/codex/usage`, `GET /v1/usage`

`POST /internal/bridge/responses` is explicitly excluded so forwarded bridge work does not double-count against the external family gate.

Why this over exact route+method keys:
- operators asked to count aliases and protocols together
- fixed keys keep validation, defaults, and UI manageable
- the current route surface is small and stable enough to maintain explicitly

### 2. Enforce limits in-process with a dedicated proxy limiter

Implement a new in-memory limiter keyed by family, using per-family counters guarded by `asyncio` synchronization. This sits in the proxy route layer rather than middleware:

- after auth and payload normalization/validation
- before upstream work or long-lived streaming/websocket handling starts

Why this over extending the existing middlewares:
- current middlewares only see coarse path buckets and are intentionally generic
- route-layer family mapping is clearer and lets `/internal/bridge/responses` bypass cleanly
- shared helpers in `app/modules/proxy/api.py` already centralize aliased workloads, so one gate can cover multiple entrypoints

### 3. Reuse dashboard settings for runtime editability

Add `proxy_endpoint_concurrency_limits` to the `dashboard_settings` row as a JSON object with fixed keys and integer values `>= 0`, where `0` means unlimited. The settings API, repository, service, frontend schemas, and mocks all expose the field.

Why this over env-only settings:
- the requested operator workflow is runtime-editable from the dashboard
- existing settings cache invalidation already gives an immediate refresh point after `PUT /api/settings`
- the values are operator policy, not deployment topology

### 4. Keep overload fail-fast and contract-preserving

When a family limit is reached:

- HTTP proxy routes return `429` with an OpenAI-style error envelope plus `Retry-After: 5`
- WebSocket proxy routes reject with close code `1013`
- no family-level queuing is introduced

If a limit is lowered below the current in-flight count, already admitted requests continue. New requests reject until the in-flight count falls below the new threshold.

Why this over adding queues:
- queues would overlap with existing bridge queue semantics and introduce head-of-line risks
- current repo conventions already use immediate overload responses for backpressure and bulkhead protections

### 5. Add explicit observability for family rejections

Rejected admissions will emit:

- a structured application log event named `proxy_endpoint_concurrency_rejected`
- a Prometheus counter `proxy_endpoint_concurrency_rejections_total{family,transport}`
- a Prometheus gauge `proxy_endpoint_concurrency_in_flight{family}`

Why this over relying only on generic 429 logs:
- operators need to distinguish family admission from quota/rate-limit 429s
- family and transport dimensions are necessary to tune settings safely

## Risks / Trade-offs

- [Risk] Route-layer enforcement can drift from the actual route surface if new proxy endpoints are added later. → Mitigation: keep the family map explicit and cover it with unit tests.
- [Risk] Runtime settings now include a nested JSON object, which increases schema and validation complexity. → Mitigation: use fixed keys, strict validation, and seed defaults of `0` for all families.
- [Risk] Responses traffic will now see two admission layers: the new family gate and the existing bridge queue/session caps. → Mitigation: keep the family gate outermost and preserve current bridge errors/metrics underneath it.
- [Risk] Per-replica limits scale total cluster capacity with replica count. → Mitigation: this is an explicit product choice for v1 and should be documented in operator-facing context.

## Migration Plan

1. Add an Alembic migration that creates `proxy_endpoint_concurrency_limits` on `dashboard_settings` and backfills all six families to `0`.
2. Extend backend settings schemas/repository/service/API to round-trip the new field and invalidate the settings cache on updates.
3. Add the in-process proxy family limiter plus logs/metrics and wire it into the shared proxy entrypoints.
4. Extend frontend settings schemas, API payload builders, UI controls, and MSW mocks.
5. Run targeted backend/frontend tests, then broader regression commands.

Rollback:
- application rollback can ignore the new field because limits default to unlimited
- DB rollback can drop the column if needed once the old app version is restored

## Open Questions

- None. This design intentionally chooses fixed family keys, per-replica semantics, dashboard editability, and fail-fast overload behavior.
