## Why

The fork is materially behind `Soju06/codex-lb` `main`, which leaves our custom `master` branch on an older upstream baseline and increases merge risk the longer it drifts. This sync also needs an evidence-based deployment workflow because production currently runs a single Docker-hosted SQLite instance where schema changes and container replacement must be coordinated carefully.

## What Changes

- Fast-forward local `main` and `fork/main` to the latest `upstream/main`.
- Merge the refreshed upstream baseline into `master`, keeping fork-specific behavior only where it is still intentional and compatible.
- Revalidate the merged result with focused migration, backend, and frontend suites before publishing `fork/master`.
- Build a deployable branch image from the merged `master` head and promote it to the VPS only after the image build succeeds.
- Add an operational rollout contract for single-host Docker + SQLite deployments so production cutovers always create an explicit pre-cutover database snapshot, preserve a rollback container, and verify a candidate image before live promotion.

## Capabilities

### New Capabilities
- `deployment-rollout-safety`: Safe single-host Docker rollout procedure for SQLite-backed codex-lb deployments, including snapshot, candidate validation, and rollback preservation.

### Modified Capabilities
- `database-migrations`: Production rollout for the container entrypoint migration path now requires an explicit operator-managed SQLite snapshot before live cutover because that path does not rely on the in-app startup backup hook.

## Impact

- Affected branches: `main`, `master`, `fork/main`, `fork/master`
- Affected systems: GitHub Actions branch image build, VPS container rollout, live SQLite database volume
- Likely affected code areas after merge review: `app/db/*`, `app/modules/proxy/*`, `app/modules/settings/*`, `app/modules/dashboard_auth/*`
- Operational risk surface: live schema advancement, container cutover timing on bound loopback ports, rollback viability after migrations
