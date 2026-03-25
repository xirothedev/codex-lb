## ADDED Requirements

### Requirement: Upstream 401 pauses the affected account immediately
When runtime proxy traffic or background account-maintenance work receives an upstream `401` for a selected account, the system MUST set that account to `paused` immediately and MUST persist an operator-readable reason describing the source of the `401`.

#### Scenario: Proxy traffic pauses an account on first upstream 401
- **WHEN** a selected account receives its first upstream `401` during proxy request handling
- **THEN** the system marks that account `paused`
- **AND** it stores reason `Auto-paused after upstream 401 during proxy traffic`

#### Scenario: Usage refresh pauses an account on first upstream 401
- **WHEN** background usage refresh receives `401` for an account
- **THEN** the system marks that account `paused`
- **AND** it stores reason `Auto-paused after upstream 401 during usage refresh`

#### Scenario: Model refresh pauses an account on first upstream 401
- **WHEN** background model refresh receives `401` for an account
- **THEN** the system marks that account `paused`
- **AND** it stores reason `Auto-paused after upstream 401 during model refresh`

### Requirement: Paused accounts stay out of routing until manual recovery
The runtime MUST exclude paused accounts from selection until an operator explicitly reactivates them. The runtime MUST NOT auto-unpause an account after later refresh attempts or scheduler cycles.

#### Scenario: Paused account is skipped by selection
- **WHEN** account selection runs while one account is `paused`
- **THEN** the paused account is not chosen for new work

#### Scenario: Manual reactivate restores a paused account to the pool
- **WHEN** an operator reactivates a paused account
- **THEN** later account selection may choose that account again

### Requirement: Current proxy requests fail over to another account after first 401
When a proxy request hits an upstream `401` at a retry-safe boundary, the system MUST pause the failed account and MUST reselect another eligible account for the current request instead of retrying the same account.

#### Scenario: Alternate account serves the retried request
- **WHEN** a request gets upstream `401` before the response is irreversibly committed
- **AND** another eligible account exists
- **THEN** the failed account is paused
- **AND** the request retries on a different account

#### Scenario: No alternate account remains after pause
- **WHEN** a request gets upstream `401`
- **AND** no other eligible account remains after pausing the failed account
- **THEN** the request fails with the normal no-accounts selection contract
