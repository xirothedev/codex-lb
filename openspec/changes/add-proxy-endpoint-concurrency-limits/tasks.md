## 1. OpenSpec and failing tests

- [x] 1.1 Add failing backend tests for family mapping, HTTP/WebSocket overload behavior, alias sharing, and internal bridge bypass.
- [x] 1.2 Add failing settings tests for `proxy_endpoint_concurrency_limits` persistence, schema validation, and `/api/settings` round-tripping.
- [x] 1.3 Add failing frontend tests for loading, editing, and saving proxy endpoint concurrency limits from the Settings page.

## 2. Backend implementation

- [x] 2.1 Add dashboard-settings persistence for `proxy_endpoint_concurrency_limits` (model, migration, repository, service, API schemas, cache invalidation).
- [x] 2.2 Implement the per-replica proxy endpoint family limiter and wire it into shared proxy entrypoints with HTTP/WebSocket fail-fast behavior.
- [x] 2.3 Add logs and Prometheus metrics for family-limit rejections and in-flight tracking.

## 3. Frontend and verification

- [x] 3.1 Extend frontend settings schemas, payload builders, API mocks, and routing-settings UI for proxy endpoint concurrency controls.
- [x] 3.2 Run targeted backend/frontend tests plus the final verification commands for the change.
