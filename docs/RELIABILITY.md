# Reliability

## Client defaults

- Timeout: 30 seconds per request (`timeout=` on `BildClient`).
- Live tests use 60 seconds.
- No automatic retries. Callers retry if they need to.
- Empty success bodies (HTTP 204 / no bytes) return `None`.
- Non-empty JSON parse failures become `{"raw": response.text}` rather
  than raising from the transport layer.

## Error mapping

| HTTP | Exception |
| --- | --- |
| 401, 403 | `BildAuthError` |
| other non-OK | `BildAPIError` |
| missing token at construct | `ValueError` |
| cannot resolve branch/version | `ValueError` |

Both API errors expose `status_code` and `payload`.

## Test strategy

- **Unit:** fake session, no network. These are the merge gate.
- **Live:** optional, read-only, skip without `BILD_API_KEY`. They catch
  drift between this client and the hosted API.
- **Harness:** docs layout, layering, taste invariants. Failures include
  remediation text.

A flake in live tests is not a reason to weaken unit tests. Skip or narrow
the live assertion; keep the route table strict.

## Header pitfall

Setting `Content-Type: application/json` on the session makes Bild 500 on
GET/DELETE (`Unexpected end of JSON input`). This is tested and linted.
See [design-docs/http-client.md](design-docs/http-client.md).
