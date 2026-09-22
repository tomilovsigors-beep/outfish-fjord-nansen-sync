# Open24 B2B reader for Outfish

Private operational helper for authorized access to https://b2b.open24.lt/.

## How it works

- Credentials are read only from Render environment variables.
- On every Render deploy/start, the service logs in to the B2B portal.
- It crawls the authenticated catalog with read-only GET requests.
- Optional `OPEN24_QUERY` filters results.
- Matching products are emitted to Render logs as `OPEN24_RESULT {...}`.
- The service then stays alive with a minimal `/health` endpoint.

## Render environment variables

- `OPEN24_USERNAME` — B2B login/email
- `OPEN24_PASSWORD` — B2B password
- `OPEN24_QUERY` — optional search/filter terms
- `OPEN24_BASE_URL` — defaults to https://b2b.open24.lt/
- `OPEN24_MAX_PAGES` — defaults to 60
- `OPEN24_MAX_RESULTS` — defaults to 150

Credentials must never be committed to GitHub.
