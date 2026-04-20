## MODIFIED Requirement: Settings page

The settings page SHALL expose API key lifecycle actions that distinguish editing metadata, renewing quota/expiry, regenerating the key secret, and deleting the key.

#### Scenario: API key renew dialog

- **WHEN** the operator opens the API key actions menu from the APIs/settings surface
- **THEN** the UI includes a dedicated `Renew` action separate from `Edit` and `Regenerate`
- **AND** the renew dialog explains that quota counters reset, the key secret stays the same, and historical logs remain available

### MODIFIED Requirement: Dashboard page

API key usage copy shown in dashboard tables and detail panes MUST distinguish lifetime request history from current-window quota counters.

#### Scenario: Renewed key still shows lifetime usage history

- **WHEN** a key has been renewed and the dashboard renders its usage summary
- **THEN** the UI labels that summary as lifetime usage (or equivalent wording)
- **AND** current-window quota counters continue to appear in the limit presentation
