# Auth

## Token sources (first match wins)

1. `BildClient(token=...)`
2. Process env `BILD_API_KEY`
3. `.env` in the current working directory or the repo root, loaded at
   import time by `_load_env_file`. Existing env vars are not overwritten.

A missing token raises `ValueError` at construct time.

## Errors

HTTP 401 and 403 raise `BildAuthError` (subclass of `BildAPIError`) with
`status_code` and `payload`. The client does not attempt a retry or a
second token.

## Issuing tokens

`client.api.users.create_token` wraps `POST users/apiToken`. That is an
account operation, not SDK configuration. Do not auto-call it from
`BildClient.__init__`.
