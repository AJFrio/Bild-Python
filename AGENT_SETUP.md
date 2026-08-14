# Bild Python — agent setup playbook

You are an agent setting up the **Bild Python SDK** for a human. This file is
the only document you need. Follow it in order. Do not declare success until
the handshake at the end returns a value.

Bild is a PDM/PLM product. This library talks to `https://api.getbild.com`
using a JWT personal access token. The package is used from source (not on
PyPI yet). Repo: `https://github.com/AJFrio/Bild-Python.git`.

## Your job

1. Ask the human for the values below. Wait for answers before installing.
2. Install the library into a virtualenv.
3. Save the token to a local `.env` (never commit it, never echo it back).
4. Call **`BildClient.verify()`** — this is the required handshake.
5. Tell the human you called that function and show the exact return value.

## What to ask the human

Ask **only** these two things, in the human's language. Do not invent
answers. Do not add extra setup questions.

### 1. Bild API token (required)

Prompt:

> I need a Bild personal access token (JWT). An admin can create one in the
> Bild web app. Tokens shown there include issued-at, issued-by, and expiry.
> Paste the token here. I will save it to a local `.env` file and will not
> commit it or print it again.

If they do not have a token, stop. Tell them to have an admin issue one in
the Bild app, then come back. Do not guess a token.

### 2. Install location (required if you are not already in this repo)

Prompt:

> Do you already have [Bild-Python](https://github.com/AJFrio/Bild-Python)
> cloned on this machine? If yes, give me the folder path. If no, tell me
> which folder I should clone it into.

Default clone URL: `https://github.com/AJFrio/Bild-Python.git`

## Do not invent a host or auth scheme

The host is always `https://api.getbild.com`. Auth is always a Bearer JWT
personal access token (`BILD_API_KEY` / `token=`).

Do **not** ask about:

- which host or endpoint to use
- AWS Lambda, staging, or any other URL
- OAuth, passwords, API keys that are not this JWT, or "custom auth"

If the human volunteers a different host or auth method, tell them this
SDK only talks to `https://api.getbild.com` with a Bild JWT, then continue
with the token they paste.

## Install

Use Python 3.10 or newer.

```bash
git clone https://github.com/AJFrio/Bild-Python.git
cd Bild-Python
python3 -m venv .venv
```

Activate:

- macOS / Linux: `source .venv/bin/activate`
- Windows: `.venv\Scripts\activate`

If `pip` is blocked (uv-managed interpreter):

```bash
uv pip install -e . --python .venv/Scripts/python.exe
```

Otherwise:

```bash
pip install -e .
```

If the repo is already cloned, skip `git clone` and install in that folder.

## Save the token

Copy `.env.example` to `.env` in the repo root (`.env` is gitignored):

```bash
BILD_API_KEY=<the token the human pasted>
```

Rules:

- Do not write the token into README, chat logs you control, or any tracked file.
- Do not `git add .env`.
- Prefer `.env` over putting the token in the shell, so later `BildClient()`
  calls work without the human pasting it again.

## Handshake (required)

From the repo root, with the venv active, run this exact code:

```python
from bild import BildClient

client = BildClient()  # reads BILD_API_KEY from .env
result = client.verify()
print(result)
```

Do not pass `base_url`. `verify()` is read-only. It calls `users.list` and
`projects.list` and returns a dict shaped like:

```python
{
    "ok": True,
    "function": "BildClient.verify",
    "base_url": "https://api.getbild.com",
    "users": <API payload>,
    "projects": <API payload>,
}
```

### What to tell the human after a success

Use this shape. Include the real `result` value. Do not omit it.

> Setup is complete. I called `BildClient.verify()` and it returned:
>
> ```
> <paste the exact result dict>
> ```
>
> The token works. I can use `client.api.<group>` for further Bild work.

### If it fails

| Error | Meaning | What you do |
| --- | --- | --- |
| `ValueError: Missing token` | `.env` not loaded or empty | Fix `.env`, retry `verify()` |
| `BildAuthError` (401/403) | Token invalid or expired | Ask for a new token; do not retry blindly |
| Other `BildAPIError` | API problem | Show `status_code` and `payload`; ask the human |

Do not declare setup complete without a successful `verify()` return value.

## After setup

You may keep using the same `BildClient()` for the human's next request.

Documented groups: `users`, `projects`, `project_users`, `branches`,
`commits`, `files`, `uploads`, `checkouts`, `shared_links`, `metadata`,
`feedback`, `packages`, `revisions`, `approvals`, `boms`, `search`,
`webhooks`.

Do **not** invite users, upload, delete, checkout, or create webhooks unless
the human explicitly asked for that write. Prefer list/get/search.

Escape hatch for an unwrapped path: `client.get("projects")`.
