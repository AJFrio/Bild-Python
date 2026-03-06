# Bild-Python

Python library for interacting with the Bild External API.

> This repo is currently intended to be used directly from source (not from PyPI yet).

## 1) Clone and set up

```bash
git clone https://github.com/AJFrio/Bild-Python.git
cd Bild-Python
python3 -m venv .venv
source .venv/bin/activate
pip install requests
```

## 2) Set your API token

```bash
export BILD_API_KEY="YOUR_JWT_TOKEN"
```

Or pass token directly in code.

## 3) Basic usage

```python
from bild import BildClient

client = BildClient()  # uses BILD_API_KEY from env
# or: client = BildClient(token="YOUR_JWT_TOKEN")

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

### Add users to your account

```python
client.api.users.add(
    emails=["person@example.com"],
    role="Member",
    projects=[{"id": "project-id", "projectAccess": "Editor"}]
)
```

### List files in a project

```python
files = client.api.files.list("project-id")
print(files)
```

### Convert a file to STL (auto-default branch + latest version)

```python
result = client.api.files.universal_format(
    project_id="project-id",
    branch_id=None,           # auto-resolves main/default branch
    file_id="file-id",
    file_version=None,        # auto-resolves latest file version
    output_format="stl"
)
print(result)
```

### Shared links

```python
links = client.api.shared_links.list("project-id")
print(links)

new_link = client.api.shared_links.create("project-id", {
    "name": "Review Link",
    "fileIds": ["file-id"]
})
print(new_link)
```

### Search

```python
search_result = client.api.search.query({"query": "bolt"})
print(search_result)
```

---

## API groups available

- `client.api.users`
- `client.api.projects`
- `client.api.project_users`
- `client.api.branches_commits`
- `client.api.files`
- `client.api.file_upload`
- `client.api.file_checkin_checkout`
- `client.api.shared_links`
- `client.api.files_move_delete`
- `client.api.files_metadata`
- `client.api.feedback_items`
- `client.api.packages`
- `client.api.revisions`
- `client.api.approvals`
- `client.api.boms`
- `client.api.search`

---

## Advanced: custom base URL

```python
client = BildClient(
    token="YOUR_JWT_TOKEN",
    base_url="https://api.portle.io/api"
)
```

## Escape hatch for unwrapped endpoints

```python
raw = client.get("projects")
print(raw)
```
