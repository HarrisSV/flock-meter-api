# Urja Meter Ops protocol notes

This document records direct, authenticated observations of the normal-user portal flows. Values such as passwords, cookies, and the export-signing key are intentionally excluded.

## Confirmed

### Authentication

- `POST /login` receives an `application/x-www-form-urlencoded` body with `email` and `password`.
- The browser request uses `X-Sveltekit-Action: true` and an `Origin` matching the portal.
- A successful action response is a SvelteKit redirect envelope: `{"type":"redirect","status":303,"location":"/meters"}`.
- Authentication is represented by the HttpOnly, Secure, `SameSite=Lax` cookie `__Secure-better-auth.session_token`, with a one-hour `Max-Age`.
- The portal is a SvelteKit application and appears to use Better Auth; the presence of `POST /api/auth/sign-out` supports this identification.

### Meter search

- `GET /portal/meters/search?q=<term>&page=<n>` returns JSON.
- The client code reads `data` and `total`; the UI calculates pages as `ceil(total / 20)`.
- Rows use `meterId`, `serialNo`, `make`, `phaseType`, `installStatus`, and `dtCode`.
- Search is server-side and debounced in the browser by 250 ms.

### Meter detail

- The server-rendered detail page includes nameplate fields and hierarchy but loads location and consumption asynchronously.
- `GET /portal/meters/{meterId}/geo` returns `{ "data": { "latitude": "...", "longitude": "..." } }`. Coordinates are strings upstream.
- `GET /portal/meters/{meterId}/energy` returns `{ "data": [...] }`, where each half-hourly reading has `timestamp` (`DD/MM/YYYY HH:mm`), `kwh`, `kvah`, and `voltR`. Measurements are strings upstream.
- The observed default response held eight days of half-hourly readings (384 records), from 23 June through 30 June 2026 for `J100000`.

### Transformers and full export

- `GET /portal/dts?page={page}` returns 20 transformer records per page, each with `code`, `name`, `feederCode`, and numeric `capacityKva`; the observed total was 40.
- `GET /portal/keys` returns an export-signing key to an authenticated normal user. The key must be treated as secret and must not be exposed by the facade.
- The portal signs its export request with HMAC-SHA256 over four newline-separated values: `GET`, `/portal/export`, `page=1`, and the Unix timestamp. It sends the timestamp and hex digest as `x-timestamp` and `x-signature` headers.
- `GET /portal/export?page=1` returns all 403 meters in `{ data, total }`. Each record adds `installType`, `build`, a seven-level hierarchy, and numeric `{ lat, lng }` geo data.

## Open questions

- Whether session expiry is sliding or requires a fresh login after exactly one hour.
- Whether energy supports undocumented filter parameters; the shipped client uses no query parameters.
- At what data volume the one-shot bulk export should become a streaming or cached job.

## Safety notes

Do not commit credentials, session cookies, copied `curl` commands containing cookies, or screenshots with secrets. Treat the portal as read-only and only use capabilities exposed to a normal logged-in user.

