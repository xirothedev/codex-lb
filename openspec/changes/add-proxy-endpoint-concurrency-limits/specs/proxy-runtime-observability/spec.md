## ADDED Requirements

### Requirement: Proxy endpoint concurrency rejections are observable
When an external proxy request is rejected by a proxy endpoint concurrency family limit, the system MUST emit an operator-visible log event and update family-specific runtime metrics. The log event MUST identify the family, transport, method, path, and rejection result. Runtime metrics MUST include a rejection counter and an in-flight gauge keyed by family.

#### Scenario: HTTP family rejection is logged and counted
- **WHEN** an HTTP proxy request is rejected because its family concurrency limit is full
- **THEN** the runtime emits a `proxy_endpoint_concurrency_rejected` log entry with the family and request metadata
- **AND** the rejection counter increments for that family and transport

#### Scenario: In-flight family gauge tracks admitted work
- **WHEN** a proxy request is admitted into a family with concurrency enforcement
- **THEN** the in-flight gauge for that family increases while the request is active
- **AND** it decreases when the request completes or disconnects
