## MODIFIED Requirements

### Requirement: Stream reservations survive alternate-account retry after upstream 401
When a streamed proxy request reserves API-key usage and then receives upstream `401` before the stream is irreversibly committed, the service MUST pause the failed account and retry on a different eligible account without double-finalizing or leaking the reservation.

#### Scenario: Stream 401 pauses failed account and retries on alternate account
- **WHEN** the first streamed attempt receives upstream `401`
- **AND** another eligible account exists
- **THEN** the failed account is paused
- **AND** the request retries on a different account
- **AND** API-key reservation settlement still occurs exactly once

#### Scenario: Stream 401 with no alternate account settles once and fails cleanly
- **WHEN** the first streamed attempt receives upstream `401`
- **AND** no other eligible account exists after pausing the failed account
- **THEN** the request fails with the normal no-accounts contract
- **AND** API-key reservation settlement still occurs exactly once
