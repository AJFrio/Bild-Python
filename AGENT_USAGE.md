# Bild Python — agent usage

You are an agent using the **Bild Python SDK** after setup. Host is always
`https://api.getbild.com`. Auth is always a Bearer JWT (`BILD_API_KEY` /
`token=`). Do not invent a host, auth scheme, or endpoint.

If setup is not done, follow [AGENT_SETUP.md](AGENT_SETUP.md) first. Call
`BildClient.verify()` before other work.

## Start every task this way

```python
from bild import BildClient

client = BildClient()  # reads BILD_API_KEY from .env
projects = client.api.projects.list()
```

Pick IDs from API responses. They are UUID v4 values. Do not invent IDs.
List payloads are often `{ "data": [ ... ], "message": "success" }`. Read
`id` (or `projectID` / `fileID` / `branchID` when that is what the item uses).

## Default branch — do not guess `main` or `master`

Bild branches are often named after the project. Names like `main` and
`master` frequently do not exist. Never ask the human for a branch id
until `resolve_branch_id` has failed.

```python
branch_id = client.resolve_branch_id(project_id)
```

That lists `GET /projects/{project_id}/branches` and picks, in order:

1. A branch flagged `isMain`, `isDefault`, `isDefaultBranch`, or `default`
2. A branch named `main` or `master` (case-insensitive)
3. The first branch in the list

You can also pass `branch_id=None` into any branch-scoped method. The SDK
resolves it the same way.

```python
files = client.api.files.list_versions(project_id, None, file_id)
boms = client.api.boms.list(project_id)  # None is the default
meta = client.api.metadata.get(project_id, None, file_id)
```

These list calls are different: omitting `branch_id` hits a **project-level**
route (the API's own default-branch / account-wide list), not a resolved
branch path:

- `client.api.files.list(project_id)` → `GET /projects/{id}/files`
- `client.api.commits.list(project_id)` → `GET /projects/{id}/commits`
- `client.api.shared_links.list(project_id)` → `GET /projects/{id}/sharedLinks`
- `client.api.revisions.list(project_id)` → `GET /projects/{id}/revisions`
- `client.api.feedback.list(project_id)` → `GET /projects/{id}/feedbackItems`

To force a specific branch on those, pass the id from `resolve_branch_id`
or `client.api.branches.list(project_id)`.

## Latest file version

```python
version_id = client.resolve_file_version(project_id, branch_id, file_id)
# or
latest = client.api.files.get_latest(project_id, None, file_id)
```

`files.export_universal(..., branch_id=None, file_version=None)` resolves
both the default branch and the latest version.

## Resource groups

Use `client.api.<group>`. Do not invent methods.

| Group | Typical calls |
| --- | --- |
| `users` | `list` |
| `projects` | `list` |
| `project_users` | `list` |
| `branches` | `list` |
| `commits` | `list`, `get` |
| `files` | `list`, `list_versions`, `get_latest`, `get_version`, `export_universal` |
| `shared_links` | `list` |
| `metadata` | `list_fields`, `get` |
| `feedback` | `list`, `get` |
| `packages` | `list`, `get` |
| `revisions` | `list`, `get`, `get_closure` |
| `approvals` | `list`, `get` |
| `boms` | `list`, `get` |
| `search` | `files("query")` — this is `PUT /search` |
| `webhooks` | `list`, `get` |

Writes (invite, upload, checkout, move, delete, release, create shared
link, create webhook) only if the human explicitly asked. Prefer
list/get/search.

## Errors

| Exception | When |
| --- | --- |
| `ValueError` | Missing token, or no branch/version could be resolved |
| `BildAuthError` | HTTP 401/403 — ask for a new JWT; do not retry blindly |
| `BildAPIError` | Other HTTP failures — show `status_code` and `payload` |

```python
from bild import BildAPIError, BildAuthError
```

## Response envelopes

- Success items usually live under `data` (sometimes `items`).
- Large lists may return `{ "s3Url": "..." }` instead of an inline array.
  GET that URL yourself. Do **not** send the Bild `Authorization` header
  to S3.
- Some writes are async. A 200 means accepted; the change may finish later.

## Escape hatch

Unwrapped path only. Do not set `Content-Type` on a shared session if you
drop to raw `requests` — Bild treats that header as "this request has a
JSON body" and GET/DELETE then 500.

```python
raw = client.get("projects")
```

## Do not

- Guess branch names (`main`, `master`, …).
- Invent hosts, tokens, or endpoints.
- Commit `.env` or print the JWT.
- Write or delete unless the human asked.
- Follow `s3Url` with the Bild bearer token.
