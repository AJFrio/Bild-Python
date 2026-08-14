# Agent map

Python SDK for the [Bild External API](https://bildexternalapi.portledocs.com/).
Read this file first, then open only the docs you need for the task.

## What this is

`bild` is a source-install client for `https://api.getbild.com`.
Callers use `BildClient` and `client.api.<group>` resource methods.
The package is not on PyPI yet.

## Start here

| If you need | Open |
| --- | --- |
| Product intent | [docs/PRODUCT.md](docs/PRODUCT.md) |
| Architecture / layers | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Coding rules | [docs/CONVENTIONS.md](docs/CONVENTIONS.md) |
| Design history | [docs/design-docs/index.md](docs/design-docs/index.md) |
| Active work | [docs/exec-plans/active/](docs/exec-plans/active/) |
| Tech debt | [docs/exec-plans/tech-debt-tracker.md](docs/exec-plans/tech-debt-tracker.md) |
| Quality grades | [docs/QUALITY_SCORE.md](docs/QUALITY_SCORE.md) |
| Security | [docs/SECURITY.md](docs/SECURITY.md) |
| Reliability | [docs/RELIABILITY.md](docs/RELIABILITY.md) |
| Full catalog | [docs/INDEX.md](docs/INDEX.md) |
| End-user agent setup | [AGENT_SETUP.md](AGENT_SETUP.md) |

## Layout

- `bild/` — SDK package (transport, errors, resource APIs)
- `tests/` — unit tests always; live API tests only if `BILD_API_KEY` is set
- `docs/` — system of record (do not put long guidance in this file)
- `tools/` — harness linters and `tools/check.py`
- `.github/workflows/ci.yml` — format, lint, typecheck, harness, tests

## Commands

```bash
python -m pip install -e ".[dev]"   # or: uv pip install -e ".[dev]"
python tools/check.py --all
```

Or one at a time: `ruff format .` · `ruff check .` · `mypy bild` · `python tools/check.py` · `pytest tests -q`

Live tests are read-only and skip unless `BILD_API_KEY` is set (or present in `.env`).

## Invariants (mechanically enforced)

1. Do not set `Content-Type` on the shared session. Bild treats that header as "this request has a JSON body"; GET/DELETE then 500.
2. Public exports stay `{BildClient, BildAPIError, BildAuthError}`.
3. Resource classes are named `*API` and attached on `_Resources`.
4. Optional JSON fields go through `_omit_none`.
5. Never commit `.env` or real tokens. Use `.env.example`.
6. Live tests must not write or delete.
7. Keep this file under 130 lines. Put detail in `docs/`.
8. After any change, run `python tools/check.py --all` and follow each `REMEDIATION:` line.

## How to change the SDK

1. Read `ARCHITECTURE.md` and the matching file under `docs/design-docs/`.
2. Add or update the method on the correct `*API` class.
3. Add a route assertion in `tests/test_client_routes.py`.
4. If the change is user-facing, update `README.md` and `docs/product-specs/python-sdk.md`.
5. Do not invent endpoints. Confirm against the Bild External API reference.

## When something fails

Harness linters print `REMEDIATION:` lines. Follow those before improvising.
If a rule is wrong, update the linter and the doc that states the rule in the same change.
