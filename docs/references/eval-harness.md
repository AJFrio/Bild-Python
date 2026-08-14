# Evaluation harness

This SDK is evaluated by executable checks, not by a separate model-eval
framework.

| Layer | Command | What it proves |
| --- | --- | --- |
| Format | `ruff format --check .` | Mechanical style |
| Lint | `ruff check .` | Standard Python defects |
| Types | `mypy bild` | Import and annotation consistency |
| Architecture / docs / taste | `python tools/check.py` | Harness invariants |
| Unit + route + live-skip | `pytest tests -q` | Client behavior |
| Live (optional) | `BILD_API_KEY=... pytest tests -q` | Hosted API still matches |

A change is not done until `python tools/check.py --all` is green.
If you add a new class of mistake agents keep making, add a linter with a
`REMEDIATION:` line rather than another paragraph in `AGENTS.md`.
