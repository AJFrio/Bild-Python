# Architecture

Top-level map of the Bild Python SDK. Layer rules are enforced by
`tools/linters/architecture.py` and `tests/test_architecture.py`.

## Purpose

Wrap the Bild External HTTP API in a small, typed-enough Python client so
scripts and apps can list projects, manage files, and call other documented
endpoints without assembling URLs and auth headers by hand.

## Layers (dependency only flows downward)

```
bild/__init__.py          public surface
        │
        ▼
bild/client.py            transport + resource APIs
        │
        ▼
bild/errors.py            exception types (no client import)
        │
        ▼
requests / stdlib
```

| Layer | Module | May import | Must not import |
| --- | --- | --- | --- |
| Public surface | `bild/__init__.py` | `client`, `errors` | `requests` directly |
| Transport + resources | `bild/client.py` | `errors`, `requests`, stdlib | nothing outside `bild` except `requests` |
| Errors | `bild/errors.py` | stdlib only | `bild.client`, `requests` |

New modules under `bild/` are allowed only if they fit this layering and are
wired into the public surface or a resource class. Do not add a second HTTP
client.

## Runtime shape

```
BildClient
  token, base_url, timeout, session
  request / get / post / put / delete
  resolve_branch_id / resolve_file_version
  verify() — read-only handshake (users + projects)
  api: _Resources
        users, projects, project_users, branches, commits, files,
        uploads, checkouts, shared_links, metadata, feedback,
        packages, revisions, approvals, boms, search, webhooks
```

Each `*API` class holds a `client: BildClient` and only issues HTTP via
`self.client`. Resource classes do not call `requests` themselves.

## HTTP contract

- Default host: `https://api.getbild.com`
- Auth: `Authorization: Bearer <token>` on every request
- `Accept: application/json` is set on the session
- `Content-Type` is **not** set on the session. `requests` adds it only when
  `json=` is passed. See [docs/design-docs/http-client.md](docs/design-docs/http-client.md).
- 401/403 → `BildAuthError`; other non-OK → `BildAPIError`

## Tests

| Suite | Role |
| --- | --- |
| `tests/test_auth.py` | token required, bearer header, no Content-Type, 401/403 |
| `tests/test_client_routes.py` | every resource method hits the expected path/method |
| `tests/test_import.py` | package import smoke |
| `tests/test_live_api.py` | read-only calls against the real API when a token is present |
| `tests/test_architecture.py` | layer and public-surface invariants |
| `tests/test_docs.py` | knowledge-base files exist and stay linked |

## Known structural debt

`bild/client.py` currently holds transport helpers and every resource class.
Splitting resources into `bild/resources/` is tracked in
[docs/exec-plans/tech-debt-tracker.md](docs/exec-plans/tech-debt-tracker.md).
Until that lands, file-size limits treat `client.py` as one module.
