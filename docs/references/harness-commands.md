# Harness commands

Install once:

```bash
python -m pip install -e ".[dev]"
```

If the interpreter is uv-managed (PEP 668), use the project venv instead:

```bash
uv pip install -e ".[dev]" --python .venv/Scripts/python.exe
.\.venv\Scripts\python.exe tools\check.py --all
```

One-shot (format check, lint, types, custom linters, tests):

```bash
python tools/check.py --all
```

Apply formatting (not used in CI; CI only `--check`s):

```bash
ruff format .
```

Individual gates:

```bash
ruff format --check .
ruff check .
mypy bild
python tools/check.py
pytest tests -q
```

Unix shortcut: `make check` (same as `python tools/check.py --all`).

Live API tests run automatically when `BILD_API_KEY` is set. They are
read-only. CI does not set that variable.
