## ADDED Requirements

### Requirement: Viewer restores valid sessions before prompting for login

When a user opens `/viewer`, the frontend SHALL check the existing viewer session before rendering the API-key login form. If the session is valid, the viewer dashboard SHALL render without requiring the user to re-enter the API key.

#### Scenario: Valid session restores viewer dashboard
- **GIVEN** the browser has a valid viewer session cookie
- **WHEN** the user opens or reloads `/viewer`
- **THEN** the viewer dashboard renders without showing the login form

#### Scenario: Unauthorized viewer response clears local auth state
- **WHEN** a viewer API request returns `401`
- **THEN** the frontend clears viewer authentication state and shows the viewer login form

### Requirement: Viewer cost quota limits render as dollars

Viewer quota limits with `limit_type: "cost_usd"` SHALL display `current_value` and `max_value` as dollars by converting stored microdollars to USD. Non-cost limits SHALL continue to use compact numeric formatting.

#### Scenario: Cost limit uses dollar formatting
- **WHEN** a viewer quota entry has `current_value: 20158733`, `max_value: 730000000`, and `limit_type: "cost_usd"`
- **THEN** the viewer displays `$20.16 / $730.00`

### Requirement: Viewer shows dashboard-equivalent 7-day usage visualization

The viewer dashboard SHALL render the same usage visualization pattern as the dashboard APIs tab for the authenticated key: an account-cost donut when account-cost buckets exist, a 7-day token/cost trend chart when trend data exists, and an accumulated toggle for the trend.

#### Scenario: Viewer shows usage trend
- **WHEN** viewer trend data contains token or cost points
- **THEN** the viewer renders a 7-day token/cost trend chart with the Tokens/Cost legend and accumulated toggle

#### Scenario: Viewer shows account-cost donut
- **WHEN** viewer 7-day usage data contains one or more account-cost buckets
- **THEN** the viewer renders the account-cost donut beside the usage trend using the APIs tab visual pattern

