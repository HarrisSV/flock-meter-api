# Flock Meter API

A small, read-only FastAPI service that gives product and data consumers a stable interface to Urja Meter Ops. It authenticates server-side and never exposes the portal's session cookie.

## Status

The service is grounded in a direct, authenticated investigation of the normal-user portal flows. It covers search, per-meter location and energy readings, and the portal's signed full export. Credentials, cookies, and the portal's transient export-signing secret remain server-side.

## Run locally

```sh
cp .env.example .env
# Put the supplied portal credentials in .env; do not commit this file.
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

The interactive API reference is at `http://127.0.0.1:8000/docs`. The OpenAPI 3 document is committed as [openapi.json](openapi.json) and also served at `http://127.0.0.1:8000/openapi.json`.

## Documents

- [PROTOCOL.md](PROTOCOL.md) — how Urja Meter Ops works under the hood (auth, data, quirks)
- [openapi.json](openapi.json) — OpenAPI 3.x description of **this** API, not the portal
- [REFLECTION.md](REFLECTION.md) — assignment reflection prompts

## Layout

- `app/` — FastAPI service (`main.py` routes, `client.py` portal adapter, `models.py` response shapes, `config.py` settings)
- `tests/` — health and schema tests that do not require a live portal
- `.env.example` — configuration template; copy to `.env` and fill the supplied portal credentials

## API

```sh
curl 'http://127.0.0.1:8000/v1/meters?q=ABC&page=1'
curl 'http://127.0.0.1:8000/v1/meters/METER-ID/geo'
curl 'http://127.0.0.1:8000/v1/meters/METER-ID/energy'
curl 'http://127.0.0.1:8000/v1/meters/export'
```

`GET /v1/meters` returns the discovered fields `meterId`, `serialNo`, `make`, `phaseType`, `installStatus`, and `dtCode`, alongside the portal's `total`. Pagination is one-based and the portal page size is 20.

## Design decisions

- The service calls the portal only with a server-side `httpx` client and its cookie jar. Browser credentials and cookies are never returned to API consumers.
- It retries once after a `401` or `403`, because the observed Better Auth session is short-lived (one hour).
- Every exposed response is typed from the observed upstream schema. Numeric strings in the upstream geo and energy responses are normalised to JSON numbers.
- The portal's bulk export requires a short-lived HMAC signature. The service obtains the key and signs the request internally; it never includes the key in a response or log.
- The external API is read-only: there are no mutating routes.

## Deliberately left out

- A persistent cache and local query index: defer them until real data volume and freshness requirements are known.
- Caching: add it only once freshness and client-volume requirements are known.
- A public write API: the source system is treated as read-only.

## Validation to finish

1. Exercise session expiry and record whether the cookie is refreshed or a fresh login is required.
2. Add recorded-response tests for every portal endpoint, including 401/403 renewal and bad signatures.
3. Decide whether the complete export should be cached or streamed when consumer volume grows.

See [PROTOCOL.md](PROTOCOL.md) for evidence and open questions, and [REFLECTION.md](REFLECTION.md) for the candidate's own reflection prompts.

