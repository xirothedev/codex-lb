---
name: codex-lb-upstream-sync-vps-deploy
description: Sync the latest official Soju06/codex-lb main branch into this improved fork, validate merge compatibility with the local master branch, and optionally build and deploy the resulting image to the VPS. Use whenever the user asks to pull in new upstream codex-lb changes, compare official main with our fork, fast-forward fork/main, merge upstream into master, validate migrations or deploy the updated codex-lb container to the VPS.
license: MIT
compatibility: Requires git, gh CLI access to xirothedev/codex-lb, and SSH access to sysadmin@165.22.63.100 for live VPS checks/deploy.
metadata:
  author: xirothedev
  version: "1.0"
---

Capture the workflow for bringing the newest official `Soju06/codex-lb` changes into this repo, validating them, and shipping them safely to the VPS.

## Defaults
- Official upstream remote: `upstream` -> `https://github.com/Soju06/codex-lb.git`
- Fork remote: `fork` -> `https://github.com/xirothedev/codex-lb.git`
- Integration branch: `master`
- Sync branch: `main`
- VPS host: `sysadmin@165.22.63.100`
- VPS container: `codex-lb-custom-server`
- VPS rollback container naming pattern: `codex-lb-custom-server-prev-<timestamp>`
- VPS data volume: `codex-lb-custom-data`
- Expected exposed loopback ports: `127.0.0.1:2457->2455` and `127.0.0.1:1457->1455`

If any of these do not match the live repo or server state, inspect first and then use the discovered values.

## When to use
Use this skill when the user asks for any of the following:
- bring the latest official `codex-lb` main changes into our repo
- compare upstream official main with our `main` or `master`
- sync `fork/main` with `upstream/main`
- merge official updates into our `master`
- check whether migrations are safe before VPS deployment
- build/push a branch image for codex-lb and deploy it to the VPS

## Workflow

### 1. Inspect repo state before changing anything
Run read-only checks first.

```bash
git status --short --branch
git remote -v
git branch -vv --all
git log --oneline --decorate -5 upstream/main
git log --oneline --decorate -5 master
```

Confirm:
- `main` tracks upstream `main`
- `master` is the branch that carries the custom improvements
- the worktree is clean before branch-changing or merging

### 2. Fetch and compare upstream vs local branches
Always fetch the true current upstream state instead of trusting stale local refs.

```bash
git fetch upstream main
git fetch fork main master
```

Then compare:

```bash
git rev-list --left-right --count upstream/main...main
git rev-list --left-right --count upstream/main...fork/main
git rev-list --left-right --count upstream/main...master
git merge-base upstream/main master
git merge-tree --write-tree master upstream/main
```

Interpretation:
- if `upstream/main...main` is `N 0`, local `main` is behind by `N`
- if `merge-tree` returns a tree hash and no conflict output, text merge is clean
- if branches overlap in changed files, inspect those files before merging

### 3. Sync `main` and publish fork `main`
Fast-forward local `main` first, then push fork.

```bash
git checkout main
git merge --ff-only upstream/main
git push fork main
```

Verify afterwards:

```bash
git status --short --branch
git log --oneline --decorate -1 main
```

### 4. Merge upstream into `master`
Go back to `master` and merge `upstream/main` non-interactively.

```bash
git checkout master
git merge --no-edit upstream/main
```

If merge conflicts appear:
- stop and inspect the exact overlapping files
- prefer preserving custom `master` behavior where it was intentional and spec-backed
- if the failure is only a stale test expectation, update the test to match the current contract
- if the failure is production behavior, fix production code and rerun validation

### 5. Validate compatibility after merge
Run focused backend, frontend, and migration suites.

Recommended backend suite:

```bash
.venv/bin/python -m pytest \
  tests/unit/test_request_decompression_middleware.py \
  tests/unit/test_request_logs_repository.py \
  tests/unit/test_request_id_middleware.py \
  tests/unit/test_model_refresh_scheduler.py \
  tests/unit/test_proxy_utils.py \
  tests/integration/test_proxy_transcriptions.py \
  tests/integration/test_proxy_compact.py \
  tests/integration/test_request_logs_filters.py \
  tests/integration/test_sticky_sessions_api.py \
  tests/integration/test_api_keys_api.py \
  tests/integration/test_usage_summary.py
```

Recommended frontend suite:

```bash
cd frontend
bun run test \
  src/features/sticky-sessions/components/sticky-sessions-section.test.tsx \
  src/features/sticky-sessions/hooks/use-sticky-sessions.test.ts \
  src/features/sticky-sessions/schemas.test.ts \
  src/test/mocks/handler-coverage.test.ts
```

Migration safety suite:

```bash
.venv/bin/python -m pytest tests/unit/test_db_migrate.py tests/integration/test_migrations.py
```

If tests fail:
- inspect the failing contract carefully
- distinguish stale tests from true regressions
- keep fixes minimal and scoped
- rerun the failing tests first, then rerun the focused suite

### 6. Commit and push post-merge fixes
If the merge required any fixups, commit them separately after validation.

Example:

```bash
git add <files>
git commit -m "test(proxy): align merged 401 failover expectations"
git push fork master
```

If there were no fixups and the merge itself should be published, push `master` directly.

## VPS migration and deployment workflow

### 7. Inspect live VPS before deploy
Read live state before changing anything.

```bash
ssh sysadmin@165.22.63.100 hostname
ssh sysadmin@165.22.63.100 'docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"'
ssh sysadmin@165.22.63.100 'docker inspect codex-lb-custom-server'
ssh sysadmin@165.22.63.100 'docker exec codex-lb-custom-server /bin/sh -c "ls -lah /var/lib/codex-lb && python -m app.db.migrate current"'
ssh sysadmin@165.22.63.100 'docker exec codex-lb-custom-server /bin/sh -c "tr ""\\0"" ""\\n"" </proc/1/environ | grep ^CODEX_LB_DATABASE_MIGRATE_ON_STARTUP="'
```

Check and report:
- current image tag running on the VPS
- current Alembic revision
- mounted volume path and DB backend in use
- whether startup migration is disabled after entrypoint pre-upgrade

### 8. Assess migration safety before deploy
Use both code inspection and live DB facts.

Inspect locally:
- `scripts/docker-entrypoint.sh`
- `app/db/migrate.py`
- `app/db/session.py`
- the newest migration file in `app/db/alembic/versions/`

Live checks to assess scope:

```bash
ssh sysadmin@165.22.63.100 'df -h /var/lib/docker /'
ssh sysadmin@165.22.63.100 'docker exec codex-lb-custom-server python -c "import sqlite3; db=sqlite3.connect(\"/var/lib/codex-lb/store.db\"); cur=db.cursor(); cur.execute(\"select count(*) from request_logs\"); print(\"request_logs_count=\" + str(cur.fetchone()[0]))"'
```

Important nuance:
- the production entrypoint runs `python -m app.db.migrate upgrade` directly before starting the app
- the SQLite backup logic in `app/db/session.py` protects the app-startup migration path, but that backup hook is not automatically used by the container entrypoint path
- always call this out explicitly in the report

### 9. Build and push the deployable image
This repo uses the manual GitHub Actions workflow `Branch Docker Image`.

```bash
gh workflow run 'Branch Docker Image' -R xirothedev/codex-lb -f ref=master -f image_tag=master-<short_sha> -f platforms=linux/amd64
gh run view <run_id> -R xirothedev/codex-lb
gh run watch <run_id> -R xirothedev/codex-lb --exit-status
```

Wait until the run is truly `success` before touching the VPS.

### 10. Deploy to VPS with rollback preserved
Pull the image first.

```bash
ssh sysadmin@165.22.63.100 'docker pull ghcr.io/xirothedev/codex-lb:master-<short_sha>'
```

Then perform the cutover while keeping the old container for rollback:

```bash
ssh sysadmin@165.22.63.100 'set -eu; \
  ts=$(date -u +%Y%m%dT%H%M%SZ); \
  docker stop codex-lb-custom-server; \
  docker rename codex-lb-custom-server codex-lb-custom-server-prev-$ts; \
  docker run -d --name codex-lb-custom-server \
    -p 127.0.0.1:2457:2455 \
    -p 127.0.0.1:1457:1455 \
    -v codex-lb-custom-data:/var/lib/codex-lb \
    ghcr.io/xirothedev/codex-lb:master-<short_sha>'
```

Do not delete the previous container during the same turn unless the user explicitly asks.

### 11. Verify VPS after deploy
Run all of these:

```bash
ssh sysadmin@165.22.63.100 'docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | grep codex-lb-custom-server'
ssh sysadmin@165.22.63.100 'docker logs --tail 200 codex-lb-custom-server'
ssh sysadmin@165.22.63.100 'docker exec codex-lb-custom-server /bin/sh -c "python -m app.db.migrate current && ls -lah /var/lib/codex-lb"'
ssh sysadmin@165.22.63.100 'curl -s -o /dev/null -w "%{http_code}\\n" http://127.0.0.1:2457/docs'
```

Confirm in the report:
- new image tag is running
- current revision equals the newest Alembic head
- app is serving traffic
- old rollback container still exists
- whether a fresh backup file was or was not created during this deploy

## Output format
Always end with a compact report covering:
- upstream commit range brought in
- whether `fork/main` and `fork/master` were updated
- merge result on `master`
- validation results and exact test suites run
- live VPS image before/after
- live DB revision before/after
- migration safety conclusion
- any operational caveat, especially the container-entrypoint backup nuance

## Guardrails
- Never trust stale local refs for "latest upstream" questions
- Prefer `git merge-tree` before an actual merge when compatibility is uncertain
- Keep production fixes minimal and evidence-based
- If a deployment image is not built yet, do not touch the VPS
- Preserve a rollback container on the VPS during cutover
- Call out if the deploy path does not create the same backup guarantees as the app-startup path
