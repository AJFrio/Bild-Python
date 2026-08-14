# Product

Bild-Python is the official-in-spirit Python client for the Bild External API.
Bild is a PDM/PLM product for CAD files, projects, revisions, approvals, and
related collaboration features.

## Who uses this

- Engineers scripting against a Bild account (list projects, export STL/STEP,
  manage shared links, search files).
- Internal tools that need a stable import (`from bild import BildClient`)
  rather than raw `requests` calls.
- Agents implementing or extending those scripts.

## What "done" looks like

A caller can:

1. Authenticate with a JWT personal access token (`BILD_API_KEY` or `token=`).
2. Reach every documented External API group through `client.api.<group>`.
3. Get `BildAuthError` on 401/403 and `BildAPIError` on other failures.
4. Rely on branch/version auto-resolution where the SDK documents it
   (`resolve_branch_id`, `resolve_file_version`, `files.export_universal`).

The package is used from source (`pip install -e .`) until it is published
to PyPI.

## Non-goals

- A second HTTP stack or async client (unless a design doc and exec plan
  land first).
- Wrapping undocumented endpoints. Use `client.get` / `post` / `put` /
  `delete` as the escape hatch.
- Storing or refreshing tokens. The app issues JWTs; this client only sends
  them.
- Write/delete live tests against a shared account.

## Source of truth for endpoints

The [Bild External API reference](https://bildexternalapi.portledocs.com/)
wins when SDK method names and HTTP paths disagree. Update the SDK to match
the reference, then update `README.md` and `docs/product-specs/python-sdk.md`.
