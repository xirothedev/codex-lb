## ADDED Requirements

### Requirement: Proxy endpoint concurrency limits are dashboard-editable
The system MUST expose `proxy_endpoint_concurrency_limits` through `GET /api/settings` and `PUT /api/settings` as a fixed-key object with the families `responses`, `responses_compact`, `chat_completions`, `transcriptions`, `models`, and `usage`. Each family value MUST be an integer greater than or equal to `0`, where `0` means unlimited. Successful updates MUST persist in dashboard settings and apply to subsequent requests without restart.

#### Scenario: Settings API returns the full family map
- **WHEN** the dashboard reads `GET /api/settings`
- **THEN** the response includes `proxy_endpoint_concurrency_limits`
- **AND** the object contains all six families with integer values

#### Scenario: Settings API update takes effect on later requests
- **WHEN** an operator submits `PUT /api/settings` with a new `proxy_endpoint_concurrency_limits` object
- **THEN** the system persists the new values
- **AND** the next external proxy request uses the updated limit for its family

### Requirement: External proxy routes enforce family-based per-replica admission
The system MUST enforce concurrency limits per replica for external proxy endpoint families only. Equivalent aliases and protocols for the same workload MUST share one family counter. The family map MUST be:

- `responses`: `POST /backend-api/codex/responses`, `POST /v1/responses`, `WEBSOCKET /backend-api/codex/responses`, `WEBSOCKET /v1/responses`
- `responses_compact`: `POST /backend-api/codex/responses/compact`, `POST /v1/responses/compact`
- `chat_completions`: `POST /v1/chat/completions`
- `transcriptions`: `POST /backend-api/transcribe`, `POST /v1/audio/transcriptions`
- `models`: `GET /backend-api/codex/models`, `GET /v1/models`
- `usage`: `GET /api/codex/usage`, `GET /v1/usage`

`POST /internal/bridge/responses` MUST NOT participate in these family counters.

#### Scenario: Responses aliases and protocols share one family counter
- **WHEN** the `responses` family limit is `1`
- **AND** one external Responses request is already admitted on any `responses` alias or protocol
- **THEN** a concurrent request on a different `responses` alias or protocol is evaluated against that same family limit

#### Scenario: Different families remain isolated
- **WHEN** the `responses` family is at capacity
- **AND** the `chat_completions` family still has available capacity
- **THEN** a new `POST /v1/chat/completions` request is admitted

#### Scenario: Internal bridge forwarding bypasses the external family gate
- **WHEN** `POST /internal/bridge/responses` forwards work for an already admitted external request
- **THEN** the system does not count that forwarded request against the `responses` family

### Requirement: Family-limit overload fails fast with existing proxy contracts
When an external proxy request is rejected because its family is at concurrency capacity, the system MUST fail fast instead of queueing the request. HTTP routes MUST return `429` with an OpenAI-style error envelope and `Retry-After: 5`. WebSocket routes MUST reject with close code `1013`. Lowering a family limit below the current in-flight count MUST NOT cancel already admitted work, but MUST continue rejecting new work until enough in-flight requests complete.

#### Scenario: HTTP family overload returns an OpenAI-style 429
- **WHEN** an HTTP proxy request arrives for a family whose per-replica concurrency limit is already full
- **THEN** the response status is `429`
- **AND** the response includes `Retry-After: 5`
- **AND** the body is an OpenAI-style error envelope describing the concurrency rejection

#### Scenario: WebSocket family overload rejects before session work starts
- **WHEN** a WebSocket proxy request arrives for a family whose per-replica concurrency limit is already full
- **THEN** the system rejects the socket with close code `1013`
- **AND** no upstream proxy session work starts for that request
