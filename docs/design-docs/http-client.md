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
stripped of a leading slash. The host is `https://api.getbild.com`.

## Resolvers

- `resolve_branch_id(project_id, branch_id=None)` — uses the given id, else
  the branch marked `isMain` / `isDefault` / `isDefaultBranch` / `default`,
  else a branch named main/master, else the first branch. IDs are read from
  `id`, `branchId`, or `branchID`.
- `resolve_file_version(...)` — uses the given version, else
  `GET .../files/{file_id}/latest`.

Branch-scoped resource methods accept `branch_id: str | None` and call
`resolve_branch_id`. Do not invent a name lookup (`main` / `master`).

These list methods keep a project-level route when `branch_id` is omitted
(`files.list`, `commits.list`, `shared_links.list`, `revisions.list`,
`feedback.list`). Pass an explicit id (or the result of `resolve_branch_id`)
to hit the branch path.

## Response helper

`_safe_json` returns parsed JSON. An empty success body (HTTP 204, or no
bytes) returns `None` so DELETE helpers are not confused with
`{"raw": ""}`. Non-empty non-JSON bodies become `{"raw": response.text}`.

`_pick_list` / `_pick_from_response` tolerate `{data: ...}` and `{items: ...}`
envelopes. Keep that tolerance at the helper layer, not copied into every
resource method.

## List envelopes that point at S3

Some list endpoints (notably `files.list`) may return `{s3Url: ...}`
instead of an inline JSON array when the result is large. The client
returns that envelope as-is and does **not** fetch the URL.

Following `s3Url` would be a second HTTP hop, usually to a signed URL
that must not receive the Bild `Authorization` header. Callers that need
the file list should GET the URL themselves (or use `client.get` only
against Bild paths). Do not add an automatic follow without a new spec.
