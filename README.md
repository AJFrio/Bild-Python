# bild-python

Python SDK for the Bild External API.

## Install

```bash
pip install -e .
```

## Quick start

```python
from bild import BildClient

client = BildClient(token="YOUR_JWT_TOKEN")
projects = client.api.projects.list()
users = client.api.users.list()
```

Or set `BILD_API_KEY`.

## Base URL

Default: `https://api.portle.io/api`

```python
client = BildClient(token="...", base_url="https://api.portle.io/api")
```

## Resource coverage

- `api.users`
- `api.projects`
- `api.project_users`
- `api.branches_commits`
- `api.files`
- `api.file_upload`
- `api.file_checkin_checkout`
- `api.shared_links`
- `api.files_move_delete`
- `api.files_metadata`
- `api.feedback_items`
- `api.packages`
- `api.revisions`
- `api.approvals`
- `api.boms`
- `api.search`

## Escape hatch

```python
client.get("projects")
client.post("custom/path", json={"x": 1})
```

## Smart defaults

For methods that require `branch_id` and/or `file_version`, you can pass `None` and the SDK will auto-resolve:

- default branch: prefers `isMain`/`isDefault`, then `main`/`master`, then first branch
- file version: resolves from `latestFileVersion`

## Notes

The SDK is intentionally modular and easy to extend.
If a tenant/version uses slightly different route names, use low-level methods and add/adjust a resource method quickly.
