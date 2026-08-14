# Security

## Tokens

Bild personal access tokens are JWTs. Treat them as secrets.

- Load from `BILD_API_KEY` or `BildClient(token=...)`.
- Local files: copy `.env.example` → `.env`. `.env` is gitignored.
- Never commit a real token, paste one into docs, or log the raw value.
- The client sends `Authorization: Bearer <token>` and does not persist
  tokens beyond process memory.

## What this client does not do

- Refresh, rotate, or introspect JWTs (except `users.create_token` as an
  API wrapper).
- Encrypt tokens at rest.
- Support OAuth browser flows.

## Live tests

`BildClient.verify()` is read-only (`users.list` and `projects.list`). It is
the handshake in [AGENT_SETUP.md](../AGENT_SETUP.md).

`tests/test_live_api.py` and `TestLiveAuth` run only when a token is present.
They must stay read-only (list/get/search). Do not add invite, upload,
delete, checkout, or webhook-create calls to the live suite.

CI does not receive `BILD_API_KEY`.

## Dependency surface

Runtime dependency is `requests` only. Do not add packages that pull in
unrelated network or crypto stacks without a design doc.
