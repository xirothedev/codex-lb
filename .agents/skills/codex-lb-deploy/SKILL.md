---
name: codex-lb-deploy
description: Build, canary, cut over, verify, and if needed roll back `xirothedev/codex-lb` deployments on the VPS. Use whenever the user asks to deploy, redeploy, release, cut over, canary, roll back, build/push the production image, inspect live VPS state, or verify migration safety before deploy. If a deploy request also includes upstream sync, do the sync first and then stay on this deploy workflow.
license: MIT
compatibility: Requires git, gh CLI access to xirothedev/codex-lb, and SSH access to sysadmin@165.22.63.100 for live VPS checks and rollout.
metadata:
  author: xirothedev
  version: "2.0"
---

Run the current production deployment workflow for this repo. Prefer the live system state over stale assumptions.

## Defaults
- Repo: `xirothedev/codex-lb`
- Branch to deploy unless the user says otherwise: `master`
- Build workflow: `Branch Docker Image`
- VPS host: `sysadmin@165.22.63.100`
- Primary container: `codex-lb-custom-server`
- Candidate container naming pattern: `codex-lb-custom-server-candidate-<short_sha>`
- Rollback container naming pattern: `codex-lb-custom-server-prev-<timestamp>`
- Data volume: `codex-lb-custom-data`
- Public loopback ports expected on the active container: `127.0.0.1:2457->2455` and `127.0.0.1:1457->1455`

## Current production assumptions to verify, not blindly trust
- Recent deploys use PostgreSQL in production, not SQLite.
- `scripts/docker-entrypoint.sh` runs `python -m app.db.migrate upgrade` before boot, then exports `CODEX_LB_DATABASE_MIGRATE_ON_STARTUP=false`.
- The GitHub Actions workflow `Branch Docker Image` is the supported image build path.
- Safe rollout keeps both a candidate container during verification and the previous stable container for rollback.

If the live host contradicts any of the above, stop assuming and report the actual state before taking the next action.

## When to use
Use this skill when the user asks for any of the following:
- deploy or redeploy codex-lb
- build and push a release image
- canary, candidate, cutover, rollout, rollback, or smoke-check the VPS
- inspect production image, container env, DB backend, or migration head before deploy
- confirm whether production still needs SQLite-to-PostgreSQL cutover work

## Workflow

### 1. Inspect the local repo state first
Run read-only checks before building or shipping anything.

```bash
git status --short --branch
git rev-parse --short=12 HEAD
git log --oneline --decorate -5 master
```

If the deploy request also includes upstream sync, fetch and merge that work before continuing with the rest of this skill.

### 2. Inspect the live VPS before changing it
Always collect these facts first.

```bash
ssh sysadmin@165.22.63.100 hostname
ssh sysadmin@165.22.63.100 'docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | grep codex-lb-custom-server'
ssh sysadmin@165.22.63.100 'docker inspect codex-lb-custom-server'
ssh sysadmin@165.22.63.100 'docker exec codex-lb-custom-server /bin/sh -c "python -m app.db.migrate current"'
ssh sysadmin@165.22.63.100 'docker exec codex-lb-custom-server /bin/sh -c "tr \"\\0\" \"\\n\" </proc/1/environ | grep ^CODEX_LB_DATABASE_"'
```

Capture and report:
- current image tag
- current Alembic revision
- live database backend from `CODEX_LB_DATABASE_URL` without exposing credentials
- whether startup migration is disabled inside the app process

### 3. Decide whether this is a normal PostgreSQL deploy or a cutover turn
Treat these as different operations.

- If the live database URL is PostgreSQL, do a normal deploy. Do not mention or perform SQLite snapshot logic unless the user explicitly asks.
- If the live database URL is SQLite, stop and follow the cutover path before claiming deploy safety.

For SQLite cutover turns, use:
- `app/db/sqlite_pg_cutover.py`
- `openspec/changes/postgres-production-cutover-and-account-log-retention/context.md`

Required cutover sequence:
1. Provision PostgreSQL and migrate it to the current head.
2. Run the sync tool in full-copy mode while SQLite production remains live.
3. Start a candidate instance against PostgreSQL on non-public ports.
4. Drain the SQLite-backed instance, run final-sync mode, then switch traffic.
5. Keep both rollback inventory items: previous app container and SQLite snapshot.

### 4. Build the deployable image through GitHub Actions
Use the manual workflow instead of ad-hoc local Docker builds.

```bash
gh workflow run 'Branch Docker Image' -R xirothedev/codex-lb -f ref=master -f image_tag=master-<short_sha> -f platforms=linux/amd64
gh run view <run_id> -R xirothedev/codex-lb
gh run watch <run_id> -R xirothedev/codex-lb --exit-status
```

Do not touch the VPS until the build run is actually `success`.

### 5. Start a candidate container first
Do not replace the active container before the candidate proves healthy.

Suggested pattern:
- pick a container name like `codex-lb-custom-server-candidate-<short_sha>`
- choose unused loopback ports before launching, for example `3457->2455` and `4457->1455`
- copy the active container environment and volume mounts, but swap only the image tag and candidate ports

Minimum checks on the candidate:

```bash
ssh sysadmin@165.22.63.100 'docker logs --tail 200 codex-lb-custom-server-candidate-<short_sha>'
ssh sysadmin@165.22.63.100 'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:<candidate-http-port>/docs'
ssh sysadmin@165.22.63.100 'docker exec codex-lb-custom-server-candidate-<short_sha> /bin/sh -c "python -m app.db.migrate current"'
```

If the candidate is unhealthy, stop there and report. Do not cut over.

### 6. Cut over while preserving rollback

#### 6a. Pre-cutover readiness gate
Before touching the active container, ALL of these MUST be true. If any fails, abort, production stays up.

- [ ] Target image present on VPS: `ssh ... 'docker image inspect ghcr.io/xirothedev/codex-lb:master-<short_sha> >/dev/null && echo OK'`
- [ ] Candidate passed `/docs` = 200 and correct Alembic head
- [ ] Full `docker run` command for new stable container is drafted with: correct image tag, public ports `127.0.0.1:2457:2455` and `127.0.0.1:1457:1455`, volume `codex-lb-custom-data:/var/lib/codex-lb`, `--restart unless-stopped`, entrypoint unchanged, env file path decided
- [ ] Active container env dumped to a VPS-local file (never echo env to transcript):

```bash
ssh sysadmin@165.22.63.100 'umask 077 && \
  docker inspect codex-lb-custom-server --format "{{range .Config.Env}}{{println .}}{{end}}" \
  | grep "^CODEX_LB_" > /tmp/codex_lb.env && wc -l /tmp/codex_lb.env'
```

#### 6b. Atomic cutover sequence (single SSH script, not separate turns)
Rename-active and start-new-stable MUST run in one script so failure cannot leave prod with zero active containers bound to `2457/1457`. Do not split this across multiple turns.

```bash
ssh sysadmin@165.22.63.100 'set -e
TS=$(date -u +%Y%m%dT%H%M%SZ)
SHA=<short_sha>
# 1. stop + rename current active (this frees public ports 2457/1457)
docker stop codex-lb-custom-server
docker rename codex-lb-custom-server codex-lb-custom-server-prev-$TS
# 2. immediately start new stable on public ports
docker run -d \
  --name codex-lb-custom-server \
  --restart unless-stopped \
  --network bridge \
  -p 127.0.0.1:2457:2455 \
  -p 127.0.0.1:1457:1455 \
  -v codex-lb-custom-data:/var/lib/codex-lb \
  --env-file /tmp/codex_lb.env \
  ghcr.io/xirothedev/codex-lb:master-$SHA > /tmp/new_cid.txt
shred -u /tmp/codex_lb.env 2>/dev/null || rm -f /tmp/codex_lb.env
echo "cid=$(cut -c1-12 /tmp/new_cid.txt) prev=codex-lb-custom-server-prev-$TS"
rm -f /tmp/new_cid.txt
'
```

Rules:
- NEVER run `docker stop codex-lb-custom-server` or `docker rename` as a standalone command without the follow-up `docker run` in the same `set -e` script. Leaving prod between rename and run = downtime.
- NEVER try to promote the candidate to production by renaming or re-binding ports. Docker port bindings are fixed at `docker run` time. A new container on public ports is required.
- Env file writes on VPS, never echoed. Wipe with `shred -u` (fallback `rm -f`) after `docker run`.
- Keep the previous stable container (`codex-lb-custom-server-prev-<timestamp>`) intact for rollback. Do not delete it during the same turn unless the user explicitly asks.

#### 6c. If the atomic script fails before `docker run` completes
Production is offline. Recover before anything else.

```bash
ssh sysadmin@165.22.63.100 'docker ps -a --format "{{.Names}}" | grep codex-lb-custom-server'
# If codex-lb-custom-server does not exist, restore prev immediately:
ssh sysadmin@165.22.63.100 'LATEST=$(docker ps -a --filter "name=codex-lb-custom-server-prev-" --format "{{.Names}}" | sort -r | head -1); \
  docker rename $LATEST codex-lb-custom-server && docker start codex-lb-custom-server'
```

The prev container preserves its original public port bindings. Starting it restores service at the old image while you investigate.

### 7. Verify the stable container after cutover
Run all of these checks:

```bash
ssh sysadmin@165.22.63.100 'docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | grep codex-lb-custom-server'
ssh sysadmin@165.22.63.100 'docker logs --tail 200 codex-lb-custom-server'
ssh sysadmin@165.22.63.100 'docker exec codex-lb-custom-server /bin/sh -c "python -m app.db.migrate current"'
ssh sysadmin@165.22.63.100 'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:2457/docs'
```

Confirm:
- the new image is running
- the revision is the expected Alembic head
- `/docs` returns `200`
- the rollback container still exists
- the candidate container is stopped or removed after the stable container is verified

### 8. Report the deploy outcome compactly
Always finish with:
- deployed commit SHA
- build run ID and resulting image tag
- VPS image before and after
- DB backend and Alembic revision before and after
- whether the turn was a normal PostgreSQL deploy or a SQLite-to-PostgreSQL cutover
- candidate result
- rollback inventory retained

## Safety rules
- Never assume production still uses SQLite. Inspect the live env first.
- Never expose raw database credentials in the response. Dump env to a VPS-local tmp file, pass via `--env-file`, then `shred -u` it. Do not `cat`, `echo`, or pipe env content through your local shell.
- Never cut over before a candidate container passes health checks.
- Never claim rollback is available unless the previous container still exists.
- Never leave production in an intermediate state at end of turn. If `codex-lb-custom-server` does not exist and is not bound to `127.0.0.1:2457` and `127.0.0.1:1457`, the turn is not done.
- Never split the rename-and-run atomic sequence across multiple turns or multiple SSH calls. One `set -e` script, or do not start at all.
- Never promote the candidate by renaming it. Public ports require a fresh `docker run` with the public port bindings.
- If the build failed, stop before touching the VPS.

## Self-inflicted outage playbook
Common ways this skill has broken production and how to avoid them.

| Failure mode | Cause | Prevention |
|---|---|---|
| Active container gone, nothing on 2457/1457 | Ran `docker stop` + `docker rename` in one turn, then paused or errored before `docker run` for new stable | Use 6b atomic script. If split is unavoidable, use 6c recovery before doing anything else. |
| Candidate "promoted" but traffic still dead | Tried to rename candidate to `codex-lb-custom-server` without changing ports. Candidate was bound to 3457/4457, not 2457/1457 | Always `docker run` a new container with public port bindings. Never rename candidate into production. |
| New stable crashes on boot, no env | Forgot `--env-file` or dumped env from wrong source container | 6a checklist enforces env dump from the current `codex-lb-custom-server` before stopping it. |
| Alembic revision mismatch after cutover | Did not inspect candidate's `python -m app.db.migrate current` before cutover | Section 5 health checks. Do not proceed to 6 without matching Alembic head. |
| Credentials leaked in transcript | Used `docker inspect ... .Config.Env` over ssh and printed output | Always redirect to VPS-local tmp file with `umask 077`, wipe with `shred -u`. |
| Rollback impossible | Deleted prev container in same turn as cutover | Keep prev until user explicitly requests cleanup in a later turn. |

## End-of-turn invariants
Before reporting success, every one of these MUST hold:

- `docker ps` shows `codex-lb-custom-server` running with ports `127.0.0.1:2457->2455/tcp, 127.0.0.1:1457->1455/tcp`
- `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:2457/docs` returns `200`
- `python -m app.db.migrate current` inside `codex-lb-custom-server` matches expected Alembic head
- At least one `codex-lb-custom-server-prev-<timestamp>` container exists (Exited, same volume + env) for rollback
- Candidate container is stopped or removed
- No tmp env file left on `/tmp` of the VPS

If any invariant fails, do not claim success. Report the actual state and the recovery step you plan next.
