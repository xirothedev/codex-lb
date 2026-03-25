## Overview

This change introduces a dedicated self-service persona for a single API key without introducing a new user table or changing how proxy authentication works.

## Decisions

### One API key is one viewer identity

Viewer login uses the existing LB API key as the only credential. The system treats each key as its own viewer identity, so no ownership migration or new viewer/user persistence is required.

### Separate viewer portal, shared presentation layer

The `/viewer` SPA surface is isolated from the admin dashboard so it cannot accidentally expose settings or account-management workflows. Shared React presentation components such as app header, stats cards, dialogs, and request-log primitives are made prop-driven where needed and reused by both portals.

### Viewer sessions are cookie-backed and scoped to `api_key_id`

After validating the supplied API key hash, the backend issues a dedicated encrypted viewer cookie containing the authenticated `api_key_id` and key prefix. All viewer endpoints derive scope from that cookie and do not trust client-supplied key identifiers.

### Raw key visibility is one-time only on regeneration

Normal viewer responses expose only `keyPrefix` and a masked display string. `POST /api/viewer/api-key/regenerate` is the only viewer endpoint that returns the new raw key. That response also rotates the viewer cookie to the regenerated key identity immediately so the portal remains logged in.

### Viewer responses hide internal LB account identifiers

Viewer request logs are filtered by `api_key_id` but do not expose `account_id` or account labels, preventing leakage of the load balancer's upstream account topology.
