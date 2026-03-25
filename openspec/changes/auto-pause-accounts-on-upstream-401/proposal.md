# auto-pause-accounts-on-upstream-401

## Why
Upstream `401` responses currently split into inconsistent behaviors. Some proxy flows force-refresh and retry the same account, some startup/background flows swallow the failure, and only refresh-token failures mark an account unusable. That leaves accounts with broken upstream auth in rotation longer than they should be and makes startup failures noisy but non-isolating.

We want a single operator-facing policy: the first upstream `401` pauses the affected account immediately, the current request fails over to another account when that retry is safe, and the paused account stays out of rotation until an operator explicitly reactivates it.

## What Changes
- Add a runtime account-health policy for upstream `401` that pauses the affected account immediately.
- Replace same-account `401 -> refresh/retry` paths with `pause -> alternate-account failover` on proxy request flows.
- Apply the same pause policy to background usage refresh and model-registry refresh cycles started during app lifespan.
- Keep permanent refresh-token failures as `DEACTIVATED`; this change only targets upstream `401` detection on account usage.

## Impact
- Bad upstream credentials are isolated on the first `401` instead of being retried repeatedly.
- Current requests prefer another healthy account instead of retrying the same one.
- The Accounts dashboard will already surface the paused status without any API shape change.
