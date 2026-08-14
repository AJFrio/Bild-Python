# HTTP client

## Session

`BildClient` uses one `requests.Session` (injected via `session=` for tests).

Session headers:

- `Authorization: Bearer <token>`
- `Accept: application/json`

Do **not** set `Content-Type` on the session. Bild's API treats that header
as "this request has a JSON body". GET and DELETE then fail with HTTP 500
and `Unexpected end of JSON input`. `requests` sets `Content-Type` only
when `json=` is passed to `session.request`.

`BildClient.request` passes `json=` only when the caller supplied a body.

## URL building

`{base_url}/{path}` with `base_url` stripped of a trailing slash and `path`
stripped of a leading slash. Default `base_url` is `https://api.getbild.com`.

## Resolvers

- `resolve_branch_id(project_id, branch_id=None)` — uses the given id, else
  the branch marked main/default, else a branch named main/master, else the
  first branch.
- `resolve_file_version(...)` — uses the given version, else
  `GET .../files/{file_id}/latest`.

Resource methods that accept `branch_id: str | None` should call
`resolve_branch_id` rather than inventing their own lookup.

## Response helper

`_safe_json` returns parsed JSON or `{"raw": response.text}`.
`_pick_list` / `_pick_from_response` tolerate `{data: ...}` and `{items: ...}`
envelopes. Keep that tolerance at the helper layer, not copied into every
resource method.
