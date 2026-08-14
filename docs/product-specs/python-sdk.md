# Spec: Python SDK

## Intent

A Python 3.10+ library named `bild` that maps the Bild External API into
resource objects on `BildClient.api`.

## Public surface

```python
from bild import BildClient, BildAPIError, BildAuthError
```

No other names are exported. Escape hatch: `client.get/post/put/delete`.

## Resource groups

Must stay aligned with `BildClient.api` and the README "API groups" list:

`users`, `projects`, `project_users`, `branches`, `commits`, `files`,
`uploads`, `checkouts`, `shared_links`, `metadata`, `feedback`,
`packages`, `revisions`, `approvals`, `boms`, `search`, `webhooks`.

## Auth

- Required token from `token=` or `BILD_API_KEY`.
- Bearer header on every request.
- `BildAuthError` on 401/403.

## Convenience (allowed)

- Load `.env` without overriding existing env.
- `resolve_branch_id(project_id, branch_id=None)` — do not guess `main` /
  `master`. Lists project branches and prefers a flagged default, then
  those names, then the first branch. Also reads `id` / `branchId` /
  `branchID`.
- Branch-scoped resource methods accept `branch_id=None` and call that
  helper. Project-level list routes (`files.list`, `commits.list`,
  `shared_links.list`, `revisions.list`, `feedback.list`) still omit the
  branch path when `branch_id` is omitted.
- `resolve_file_version` / `files.export_universal` auto-resolve latest
  version when `file_version` is omitted.
- Omit `None` optional JSON fields.
- `BildClient.verify()` — read-only handshake (`users.list` + `projects.list`)
  used by [AGENT_SETUP.md](../../AGENT_SETUP.md). Return shape is
  `{ok, function, base_url, users, projects}`.
- Consumer-agent playbooks: [AGENT_SETUP.md](../../AGENT_SETUP.md) then
  [AGENT_USAGE.md](../../AGENT_USAGE.md).

## Convenience (not allowed without a new spec)

- Async client
- Automatic pagination objects
- Retry/backoff middleware
- Code generation from an OpenAPI file (unless an exec plan replaces this
  hand-written mapping)

## Acceptance

- `python tools/check.py --all` passes.
- `tests/test_client_routes.py` covers each new method.
- README example still runs from a source install.
