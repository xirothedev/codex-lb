## ADDED Requirements

### Requirement: API-key usage survives account deletion

Deleting an account MUST NOT remove request-log rows that were authenticated by an API key. API-key usage summaries, trends, and totals that aggregate from `request_logs.api_key_id` MUST remain unchanged after the linked account row is deleted.

#### Scenario: Deleting an account keeps API-key usage totals

- **GIVEN** one or more `request_logs` rows reference both an `account_id` and an `api_key_id`
- **WHEN** the linked account is deleted
- **THEN** the `request_logs` rows remain present
- **AND** API-key usage totals derived from `request_logs.api_key_id` do not decrease

#### Scenario: Deleted account logs no longer require a live account row

- **GIVEN** an API-key-authenticated request log references account `acc_123`
- **WHEN** account `acc_123` is deleted
- **THEN** the log remains queryable for API-key usage reporting without requiring a surviving `accounts` row
