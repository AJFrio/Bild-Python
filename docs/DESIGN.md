# Design

Principles that should survive individual PRs. Encode new ones in linters
when they stop being optional.

## Progressive disclosure

Agents start at `AGENTS.md` (~100 lines) and open docs on demand. Do not
grow `AGENTS.md` into a manual. Put history and detail under `docs/`.

## Mechanical enforcement over prose

If a rule matters, a linter or structural test must fail when it is broken,
and the error must tell the agent how to fix it. Docs explain *why*.

## Thin client, thick API docs

The SDK is a faithful, boring mapping of the HTTP API:

- Python methods are `snake_case`.
- JSON keys stay Bild's `camelCase` at the wire.
- Helpers exist only where the API is awkward (default branch, latest
  file version, omitting null optional fields).

## One session, one host

`BildClient` owns one `requests.Session`, one base URL, and one token.
Resource classes do not create their own sessions.

## Fail at the boundary

Auth and HTTP errors are raised as typed exceptions with `status_code` and
`payload`. Do not swallow errors or return `None` for failed calls.

## Taste invariants

Enforced in `tools/linters/taste.py`:

- Library code does not `print`.
- Library code does not `time.sleep`.
- No secrets in tracked files.
- File size stays under the configured limit (see tech-debt tracker if
  `client.py` is the outlier).
