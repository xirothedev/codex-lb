## Context

`master` carries local improvements on top of an older upstream baseline, while production is a single Docker container running against a SQLite database volume. The current container entrypoint runs `python -m app.db.migrate upgrade` before starting the app and then disables the in-app startup migration path, so production deploys cannot assume the same automatic SQLite pre-migration backup behavior used by `app/db/session.py`.

## Goals / Non-Goals

**Goals:**
- Bring `main` and `master` onto the current upstream baseline with the smallest necessary local fixups.
- Keep merge validation focused on migration safety and the fork-specific surfaces most likely to regress.
- Publish a deterministic image tag from the merged `master` head.
- Deploy to the VPS with a rollback container preserved and a restorable SQLite snapshot created before live schema changes.

**Non-Goals:**
- Re-architect the VPS for true zero-downtime switching in this change.
- Re-spec every upstream feature carried in by the merge.
- Replace SQLite in production as part of this sync.

## Decisions

### Merge directly on `master` after refreshing `main`

The requested workflow updates `main` first so `fork/main` mirrors `upstream/main`, then merges `upstream/main` directly into `master`. Any conflict resolution or post-merge fixup stays minimal and is justified by tests or explicit fork behavior, not by opportunistic refactors.

### Validate the merge with migration-first gates

The merged tree must pass `python -m app.db.migrate check` and targeted migration tests before broader proxy and frontend checks. This catches Alembic graph problems and schema drift early, before time is spent on unrelated regressions.

### Build once from the validated `master` head

The GitHub Actions `Branch Docker Image` workflow is the release artifact source. The VPS rollout uses only the resulting `ghcr.io/xirothedev/codex-lb:master-<short_sha>` image after the workflow has completed successfully.

### Use an explicit SQLite snapshot for rollback, not the old container alone

The live database is already ahead of the last deployed image once new Alembic revisions are applied. A preserved rollback container is still useful, but it is insufficient by itself after schema advancement. The deploy workflow therefore creates a pre-cutover SQLite snapshot and treats that snapshot as the rollback source of truth.

### Use a snapshot-backed candidate container before live cutover

Because the live host ports are bound directly by the production container and the live volume is SQLite, a candidate container cannot safely share the active database file while production is serving. The rollout instead starts a candidate container on alternate loopback ports against the pre-cutover snapshot database, verifies startup and health there, and only then performs a fast live swap on the real ports.

## Risks / Trade-offs

- [Risk] Direct merge on `master` increases the blast radius of conflict resolution. -> Mitigation: refresh refs first, inspect the merge surface, keep fixes minimal, and gate on focused suites before push/deploy.
- [Risk] Snapshot-backed canary cannot fully simulate concurrent access patterns against the live SQLite file. -> Mitigation: use it only for startup, migration, and health validation, then keep the live port swap short and verify immediately after cutover.
- [Risk] Single-host Docker with fixed host ports cannot provide strict zero downtime. -> Mitigation: pre-pull the image, validate the candidate ahead of time, and minimize the stop/start window during the final swap.

## Migration Plan

1. Refresh `upstream` and `fork` refs, fast-forward `main`, and publish `fork/main`.
2. Merge `upstream/main` into `master`, resolve conflicts, and validate the merged tree locally.
3. Push `fork/master`, build `master-<short_sha>` with the branch image workflow, and wait for success.
4. On the VPS, inspect the live container and DB revision, create a pre-cutover SQLite snapshot, and verify a candidate container on alternate loopback ports against that snapshot.
5. Perform the live swap by replacing the production container, preserving the previous container name as rollback inventory.
6. Verify the new image, Alembic revision, and `/docs` health on the live ports. If cutover fails after migration, restore the SQLite snapshot before restarting the previous image.

## Open Questions

- None. The rollout targets minimal downtime on the current single-host Docker topology rather than adding new switching infrastructure.
