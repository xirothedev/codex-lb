## ADDED Requirements

### Requirement: Viewer-safe API key metadata

The system SHALL expose a viewer-safe API key representation for self-service routes that includes metadata, limits, and usage summary for a single authenticated key while omitting the raw key value.

#### Scenario: Viewer metadata omits raw key

- **WHEN** a viewer fetches API key metadata for their authenticated key
- **THEN** the response includes `id`, `name`, `keyPrefix`, limits, usage summary, and masked display content
- **AND** the raw API key is not returned
