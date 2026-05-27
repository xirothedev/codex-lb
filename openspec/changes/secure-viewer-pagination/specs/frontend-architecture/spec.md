## ADDED Requirements

### Requirement: Viewer Must Not Render Account Identity Breakdown

The viewer dashboard SHALL NOT render account-level usage breakdowns or account identity labels.

#### Scenario: Usage data contains account buckets

- **GIVEN** the viewer usage response contains aggregate 7-day usage data
- **WHEN** the viewer dashboard renders the usage panel
- **THEN** it renders the token/cost trend visualization
- **AND** it does not render account emails, account identifiers, or an account-cost donut

### Requirement: Viewer Logs Must Provide Pagination Controls

The viewer dashboard SHALL provide request-log pagination controls backed by `/viewer/logs` pagination metadata.

#### Scenario: User navigates request logs

- **GIVEN** the viewer logs response has more than one page
- **WHEN** the user clicks the next-page control
- **THEN** the frontend requests the next page from `/viewer/logs`
- **AND** the table renders that page's request logs
