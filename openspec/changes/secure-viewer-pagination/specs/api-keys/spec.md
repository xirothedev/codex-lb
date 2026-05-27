## ADDED Requirements

### Requirement: Viewer Usage Endpoint Must Not Expose Account Buckets

The `/viewer/usage-7d` endpoint SHALL return only aggregate 7-day usage totals for the authenticated API key and SHALL NOT expose account identifiers, account emails, deleted-account status, or per-account cost buckets.

#### Scenario: Viewer receives aggregate usage without account details

- **GIVEN** a viewer session is authenticated for an API key with request logs attributed to one or more accounts
- **WHEN** the viewer requests `/viewer/usage-7d`
- **THEN** the response includes the authenticated key's aggregate totals
- **AND** `account_costs` is an empty list

### Requirement: Viewer Request Logs Must Be Page-Paginated

The `/viewer/logs` endpoint SHALL accept `page` and `page_size` query parameters and SHALL return pagination metadata for the authenticated API key's request logs.

#### Scenario: Viewer requests a middle page of logs

- **GIVEN** a viewer session is authenticated for an API key with more request logs than fit on one page
- **WHEN** the viewer requests `/viewer/logs?page=2&page_size=10`
- **THEN** the response contains the second page of logs ordered by newest request first
- **AND** the response includes `page`, `page_size`, `total`, `total_pages`, `has_next`, and `has_previous`
- **AND** logs for other API keys are excluded
