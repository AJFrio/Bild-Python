# Conventions

## Python

- Require Python 3.10+.
- Use `from __future__ import annotations` in new modules.
- Public names: `BildClient`, `BildAPIError`, `BildAuthError`.
- Resource classes: `UsersAPI`, `FilesAPI`, … — suffix `API`, attached on
  `_Resources`.
- Methods: `snake_case`. JSON body keys: Bild `camelCase`.
- Drop unset optional fields with `_omit_none`.
- Resource methods named `list` must annotate collections as `Sequence[...]`
  (from `collections.abc`), not `list[...]`. The method name shadows the
  builtin and mypy then rejects `list[str]` as a type.

## Files

| Path | Role |
| --- | --- |
| `bild/__init__.py` | re-exports only |
| `bild/errors.py` | exceptions only; no `requests`, no client import |
| `bild/client.py` | transport + resource classes until the split lands |
| `tests/test_*.py` | one concern per file |
| `examples/` | runnable scripts (not collected as tests) |
| `tools/linters/` | harness rules with remediation text |

Do not add `bild/utils.py` dumping grounds. Shared helpers stay next to the
only caller, or become a named module with a design doc.

## HTTP methods

Match the External API. Several "write" operations are `PUT` (invite, move,
delete files, search). Do not "fix" them to `POST`.

## Tests

- Unit tests use a fake session. They must not need a network or token.
- Route tests assert path suffix, method, and important JSON/query fields.
  `tests/test_client_routes.py` must call every public `*API` method.
- Live tests (`tests/test_live_api.py`) are read-only and skip without
  `BILD_API_KEY`.
- Prefer `unittest` for class-scoped live setup; pytest collects both.

## Docs

- Update `docs/INDEX.md` when adding a doc.
- Keep `AGENTS.md` under 130 lines.
- User-facing snippets live in `README.md`. Runnable scripts live in
  `examples/`.
