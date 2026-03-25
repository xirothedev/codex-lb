## MODIFIED Requirements

### Requirement: HTTP Responses routes preserve upstream websocket session continuity
When a bridged HTTP Responses session hits an upstream `401` during a retry-safe connect or reconnect boundary, the service MUST pause the failed account immediately and reconnect that bridge on a different eligible account instead of forcing a same-account refresh/retry.

#### Scenario: Bridged HTTP Responses reconnect fails over after 401
- **WHEN** an HTTP bridge connect or reconnect attempt gets upstream `401`
- **THEN** the failed account is paused
- **AND** the bridge reconnects on a different account when one is available

### Requirement: Direct compact transport preserves same-contract failover on 401
The service MUST fulfill `/backend-api/codex/responses/compact` and `/v1/responses/compact` by calling the upstream `/codex/responses/compact` endpoint directly. If direct upstream compact execution returns `401` before a valid compact JSON payload is accepted, the service MUST pause the failed account and retry the same compact request on a different eligible account instead of refreshing and retrying the same account.

#### Scenario: Compact request fails over to a different account after 401
- **WHEN** the upstream `/codex/responses/compact` call returns `401` before a valid compact JSON payload is accepted
- **THEN** the failed account is paused
- **AND** the compact request retries on a different eligible account
