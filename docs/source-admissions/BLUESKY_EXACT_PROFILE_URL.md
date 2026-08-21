# Bluesky exact profile URL admission

Reviewed: 2026-08-21

PersonaLattice may use an explicit canonical `https://bsky.app/profile/<handle>` URL as another entry point to the already-active Bluesky public-profile source. The URL does not authorize broader Bluesky collection.

The adapter accepts only HTTPS `bsky.app` URLs with exactly `profile` plus one canonical handle segment. DID profile URLs, post URLs, encoded handles, credentials, custom ports, queries and fragments are rejected before provider execution. The handle still passes the existing AT-handle normalizer and reserved/non-public TLD checks.

Execution reuses the official unauthenticated `app.bsky.actor.getProfile` lookup and the existing process-owned 30 requests/minute budget shared with username research. The retained fields remain DID, normalized handle, optional bounded display name, public-web/account-candidate state and `identity_claim=false`. Posts, graphs, feeds, activity and contact data are not requested.

Public-web opt-out and unavailable-account behavior is unchanged. This extension adds no new lead-promotion rule and no second provider or quota bucket.
