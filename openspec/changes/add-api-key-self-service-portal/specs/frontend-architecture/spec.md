## ADDED Requirements

### Requirement: Separate viewer portal route

The frontend SHALL expose a separate `/viewer` portal for self-service API-key users while preserving the existing admin SPA routes and auth gate.

#### Scenario: Viewer portal route

- **WHEN** a user navigates to `/viewer`
- **THEN** the SPA renders the viewer login or viewer dashboard without exposing admin-only navigation items or settings routes

### Requirement: Shared component reuse across admin and viewer portals

The frontend SHALL reuse shared presentational components for header, stats, dialogs, and request-log rendering where possible, while keeping viewer-specific data hooks and auth state separate from admin state.

#### Scenario: Viewer route reuses shared request-log UI

- **WHEN** the viewer dashboard renders request logs
- **THEN** it reuses the shared request-log table and filter primitives with viewer-safe props instead of duplicating a parallel table implementation
