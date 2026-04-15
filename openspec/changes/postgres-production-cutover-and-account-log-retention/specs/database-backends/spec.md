## ADDED Requirements

### Requirement: SQLite-to-PostgreSQL cutover tooling is available

The project MUST provide an operator-invoked tool that copies durable codex-lb data from a SQLite database into a PostgreSQL database configured with the current schema.

The tool MUST support:

- an initial full copy into PostgreSQL
- a final sync pass that refreshes mutable state tables and appends newly created history rows

The tool MUST skip transient runtime tables whose contents can be rebuilt after restart.

#### Scenario: Initial full copy seeds PostgreSQL

- **WHEN** an operator runs the cutover tool in full-copy mode against a SQLite source and empty PostgreSQL target
- **THEN** durable codex-lb tables are copied into PostgreSQL
- **AND** preserved primary keys remain stable so later sync passes can append new history rows safely

#### Scenario: Final sync refreshes mutable state and appends history

- **GIVEN** PostgreSQL was already seeded by an earlier full copy
- **WHEN** an operator runs the cutover tool in final-sync mode during production cutover
- **THEN** mutable state tables are synchronized to the latest SQLite contents
- **AND** history tables append only rows created after the earlier full copy
- **AND** transient runtime tables remain excluded from the sync
