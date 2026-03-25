## Overview

This change introduces a single runtime primitive for upstream-auth isolation: pause an account on the first upstream `401`, persist a source-specific reason, and immediately remove that account from further routing until an operator reactivates it.

## Decisions

### Upstream `401` means pause, not refresh-and-retry

When a request, usage refresh cycle, or model refresh cycle receives an upstream `401`, the service pauses that account immediately. It does not attempt a same-account refresh/retry first.

### Manual recovery only

Paused accounts remain out of the routing pool until an operator performs the existing manual recovery flow, such as re-auth/import and `reactivate`. The runtime does not auto-unpause accounts.

### Fail over the current request when the transport boundary is safe

For proxy request paths that have not committed irreversible client output, the service reselects another account and retries on that alternate account. The failed account is excluded from reselection for the current request.

### Permanent refresh-token failures stay deactivated

`RefreshError(is_permanent=True)` continues to map to `DEACTIVATED`. This preserves the stronger operator signal for revoked/reused/expired refresh tokens and keeps the new pause policy scoped to upstream `401` detection.

### Persist operator-readable pause reasons

Paused accounts store a stable `deactivation_reason` so operators can distinguish where the `401` came from:
- `Auto-paused after upstream 401 during proxy traffic`
- `Auto-paused after upstream 401 during usage refresh`
- `Auto-paused after upstream 401 during model refresh`
