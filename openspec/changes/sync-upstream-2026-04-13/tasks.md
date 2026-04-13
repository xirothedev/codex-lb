## 1. OpenSpec and merge preparation

- [ ] 1.1 Record the upstream sync proposal, rollout design, and spec deltas for this maintenance change.
- [ ] 1.2 Refresh `upstream` and `fork` refs, confirm the worktree is clean, and capture the merge surface between `upstream/main`, `main`, and `master`.
- [ ] 1.3 Fast-forward local `main` to the latest `upstream/main` head and publish `fork/main`.

## 2. Master integration and validation

- [ ] 2.1 Merge `upstream/main` into `master`, resolve any conflicts with minimal fork-specific fixups, and keep the resulting branch on a deterministic validated head.
- [ ] 2.2 Run migration validation with `python -m app.db.migrate check` plus targeted migration tests, then rerun any failing subset after fixups.
- [ ] 2.3 Run the focused backend and frontend suites that cover the fork-specific proxy, logging, sticky-session, API key, and UI surfaces most exposed by the merge.
- [ ] 2.4 Push the validated `master` result to `fork/master`.

## 3. Image build and VPS rollout

- [ ] 3.1 Build `ghcr.io/xirothedev/codex-lb:master-<short_sha>` from the validated `master` head with the `Branch Docker Image` workflow and wait for success.
- [ ] 3.2 Inspect the live VPS container and database state, create a pre-cutover SQLite snapshot, and verify a candidate container on alternate loopback ports against that snapshot.
- [ ] 3.3 Replace the live container with the new image, preserve the previous container for rollback, and verify the final image tag, Alembic revision, and `/docs` health on the production ports.
