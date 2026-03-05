# bild-python

Clean Python SDK for the Bild External API.

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

You can also use `BILD_API_KEY` environment variable.

## Base URL

Defaults to:

- `https://api.portle.io/api`

Override with:

```python
client = BildClient(token="...", base_url="https://api.portle.io/api")
```

## Implemented modules

- `api.users`
  - `list()`
  - `add(emails, role="Member", projects=[])`
- `api.projects`
  - `list()`
  - `users(project_id)`
  - `files(project_id)`
- `api.files`
  - `latest_version(project_id, branch_id, file_id)`
  - `to_stl(project_id, branch_id, file_id, file_version=...)`
  - `to_step(project_id, branch_id, file_id, file_version=...)`
- `api.metadata`
  - `fields()`
  - `file_metadata(project_id, branch_id, file_id)`
- `api.search`
  - `query(payload)`

## Low-level escape hatch

```python
client.get("projects")
client.post("some/path", json={"x": 1})
```

## Notes

This SDK was rebuilt from scratch and focuses on a stable core + easy extension.
If an endpoint path differs in your tenant/version, use low-level methods and extend resource methods quickly.
