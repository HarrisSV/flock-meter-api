# Reflection

## What assumptions did you make?

The portal's browser Network traffic is the source of truth for auth, search, geo, energy, and export. Credentials stay server-side. The session cookie is short-lived, so a single retry after 401/403 is enough for a first version. Search pagination is one-based with a page size of 20 because that is what the UI uses. Energy is fetched with no extra query parameters because the observed client did the same. The export-signing secret is a normal-user capability, so using it internally is allowed as long as it never leaves the service.

## Which part was the most difficult, and how did you get unstuck?

The signed bulk export. Search, geo, and energy are ordinary authenticated GETs; export requires HMAC-SHA256 over method, path, query, and timestamp, plus a key from `/portal/keys`. Matching that payload exactly (newlines, `page=1`, Unix timestamp, hex digest in `x-signature`) was the part that needed careful observation rather than guesswork.

## If you had another day, what would you improve?

Recorded-response tests for login, 401/403 renewal, and a bad export signature. Confirm whether the one-hour session is sliding. Decide whether `/v1/meters/export` should stream or cache once more than one consumer hits it. Optionally expose the transformer list and a reconstructed hierarchy tree; the export payload already contains the seven-level hierarchy.

## What mistake did you make while solving this?

Treating the portal as a conventional JSON API first. Login is a SvelteKit form action (`X-Sveltekit-Action: true`) that returns a redirect envelope, not a token body. Geo and energy also send numeric values as strings. Modelling those as numbers in the facade, and authenticating the way the browser actually does, unblocked the rest of the client.

## If you were reviewing your own submission, what would you criticise?

The live-portal paths are not covered by tests, so a change in Better Auth cookies or export signing would fail at runtime. Session expiry behaviour is still an open question. There is no cache, no local query layer, and no transformer endpoint even though `/portal/dts` exists. That is sized for a 4–6 hour slice, but it is the first thing a reviewer should probe.
