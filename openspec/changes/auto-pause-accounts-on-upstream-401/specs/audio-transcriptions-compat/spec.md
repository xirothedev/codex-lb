## MODIFIED Requirements

### Requirement: Transcription requests fail over after upstream 401
When an upstream transcription request returns `401`, the service MUST pause the failed account immediately. If the request is still at a retry-safe boundary and another eligible account exists, the service MUST retry the transcription on that different account instead of refreshing and retrying the same account.

#### Scenario: Transcription 401 retries on a different account
- **WHEN** the first transcription attempt returns `401`
- **AND** another eligible account exists
- **THEN** the failed account is paused
- **AND** the retry uses a different account

#### Scenario: Transcription 401 returns no-accounts when pool is exhausted
- **WHEN** a transcription attempt returns `401`
- **AND** no other eligible account exists after pausing the failed account
- **THEN** the request returns the normal no-accounts selection error
