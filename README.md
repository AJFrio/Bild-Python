# Bild-Python

Python library for the [Bild External API](https://bildexternalapi.portledocs.com/#/docs/apireference?api_page=introduction&product_version=77).

> This repo is currently intended to be used from source (not published to PyPI yet).

To have an agent install this for you, give it [AGENT_SETUP.md](AGENT_SETUP.md).
It will ask for a Bild JWT, install the library, call `BildClient.verify()`,
and show you the return value.

## 1) Clone and set up

```bash
git clone https://github.com/AJFrio/Bild-Python.git
cd Bild-Python
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

## 2) Authenticate

Bild APIs require a **JWT personal access token**. Admin users can issue one in the Bild web app. Tokens issued in the app are listed there with issued-at, issued-by, and expiry.

The client sends that token on every request as:

```text
Authorization: Bearer <your_token>
```

Copy `.env.example` to `.env` and set the token (`.env` is gitignored):

```bash
BILD_API_KEY=YOUR_JWT_TOKEN
```

`BildClient()` loads `.env` automatically. You can also set the variable in the shell:

```bash
export BILD_API_KEY="YOUR_JWT_TOKEN"
```

```powershell
$env:BILD_API_KEY = "YOUR_JWT_TOKEN"
```

Or pass it directly:

```python
from bild import BildClient

client = BildClient(token="YOUR_JWT_TOKEN")
```

`BildClient()` with no arguments reads `BILD_API_KEY`. A missing token raises `ValueError`. Invalid or expired tokens raise `BildAuthError` (HTTP 401/403). Other failed responses raise `BildAPIError`.

Default API host: `https://api.getbild.com`.

## 3) Basic usage

```python
from bild import BildClient

client = BildClient()  # uses BILD_API_KEY from env

projects = client.api.projects.list()
print(projects)
```

---

## Common examples

### List users and projects

```python
from bild import BildClient

client = BildClient()

users = client.api.users.list()
projects = client.api.projects.list()

print("Users:", users)
print("Projects:", projects)
```

### Invite users to your account

```python
client.api.users.invite(
    emails=["person@example.com"],
    projects=[{"id": "project-id", "projectAccess": "Editor"}],
    pdm_role="Member",
)
```

### List files in a project

```python
files = client.api.files.list("project-id")
print(files)
```

### Convert a file to STL (auto-default branch + latest version)

```python
result = client.api.files.export_universal(
    project_id="project-id",
    branch_id=None,  # auto-resolves main/default branch
    file_id="file-id",
    output_format="stl",
)
print(result)
```

### Shared links

```python
links = client.api.shared_links.list("project-id")
print(links)

new_link = client.api.shared_links.create_live(
    "project-id",
    "branch-id",
    name="Review Link",
    file_ids=["file-id"],
)
print(new_link)
```

### Search

```python
search_result = client.api.search.files("bolt")
print(search_result)
```

---

## API groups

These map to the groups in the [Bild External API reference](https://bildexternalapi.portledocs.com/#/docs/apireference?api_page=introduction&product_version=77):

- `client.api.users` — account users (list, invite, update, remove, create_token)
- `client.api.projects` — list projects
- `client.api.project_users` — add / update / remove project access
- `client.api.branches` — list branches
- `client.api.commits` — list/get commits
- `client.api.files` — list files/versions, export STL/STEP, move, delete
- `client.api.uploads` — initiate / complete file upload
- `client.api.checkouts` — checkout, cancel, initiate/complete check-in
- `client.api.shared_links` — list, create live/static links, refresh, delete
- `client.api.metadata` — metadata fields and file metadata
- `client.api.feedback` — feedback items and attachments
- `client.api.packages` — account and project packages
- `client.api.revisions` — list/get/release/cancel revisions
- `client.api.approvals` — list/get/close approvals
- `client.api.boms` — list/get/download BOMs
- `client.api.search` — search files
- `client.api.webhooks` — webhook subscriptions

---

## Advanced: custom base URL

```python
client = BildClient(token="YOUR_JWT_TOKEN", base_url="https://api.getbild.com")
```

## Escape hatch for unwrapped endpoints

```python
raw = client.get("projects")
print(raw)
```

## Tests and development

```bash
python -m pip install -e ".[dev]"
python tools/check.py --all
```

That runs format check, ruff, mypy, harness linters, and pytest. Agents should start at [AGENTS.md](AGENTS.md); the knowledge base lives in [docs/INDEX.md](docs/INDEX.md).

If `BILD_API_KEY` is set (or present in `.env`), live read-only tests also run against the real API (`users`, `projects`, `files`, `search`, and the other list/get groups). Write and delete calls are not exercised.
