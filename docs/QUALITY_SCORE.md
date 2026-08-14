# Quality score

Grades are for agents and humans deciding where to invest. Update this file
when a grade changes. A = solid and enforced; B = works, some gaps;
C = usable but thin; D = missing or stale.

| Area | Grade | Notes |
| --- | --- | --- |
| Auth / token loading | B | Env + `.env` + constructor. No expiry awareness. |
| HTTP transport | B | Header contract, errors, empty bodies tested. No retries or pagination helpers. |
| Resource coverage | A | Route tests cover the documented groups. |
| Types | C | Runtime hints only; mypy is not strict on untyped defs. |
| Unit tests | A | Auth, transport, resolvers, and per-group route table with method/body asserts. |
| Live tests | B | Read-only, skip without key. Account-data dependent; `s3Url` lists skipped. |
| Docs / agent map | A | `AGENTS.md` + `docs/` catalog, linted. |
| Packaging | B | setuptools, source install. Not on PyPI. |
| Lint / format | A | ruff + custom harness linters in CI. |
| Security | B | `.env` gitignored; no token refresh or scoped helpers. |

## Gaps to close next

1. Split `bild/client.py` into transport + `bild/resources/` (tech debt).
2. Tighten mypy (`check_untyped_defs`) after the split.
3. Publish to PyPI when the public surface is stable.

See [exec-plans/tech-debt-tracker.md](exec-plans/tech-debt-tracker.md).
