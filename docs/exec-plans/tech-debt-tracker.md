# Tech debt tracker

| ID | Item | Why it exists | Suggested fix | Severity |
| --- | --- | --- | --- | --- |
| TD-1 | `bild/client.py` holds transport and every `*API` class | Fast first implementation | Split transport vs `bild/resources/*.py`; keep public imports stable | Medium |
| TD-2 | `FakeResponse` / fake session duplicated in tests | Tests grew independently | Shared `tests/fakes.py` | Low |
| TD-3 | mypy does not use `check_untyped_defs` | Current helpers are loosely typed | Annotate helpers after TD-1, then tighten | Low |
| TD-4 | Package not published to PyPI | Still source-install | Release process + version policy | Low |
| TD-5 | No retries / pagination helpers | API wrappers stay thin | Add only with a design doc and tests | Low |

Do not add debt here without an owner-less next step. Close rows when the
fix merges.
