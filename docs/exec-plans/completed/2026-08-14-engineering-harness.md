# Completed: engineering harness scaffold

**Date:** 2026-08-14

## Goal

Make this repository agent-legible using OpenAI's harness-engineering
pattern: short `AGENTS.md`, `docs/` as system of record, mechanical
enforcement (ruff, mypy, custom linters, structural tests), and CI that
runs the full loop.

## Shipped

- `AGENTS.md` map and `ARCHITECTURE.md`
- `docs/` catalog, design docs, product spec, quality grades, plans
- `tools/linters/` + `tools/check.py`
- ruff / mypy / pytest via `.[dev]`
- structural tests and expanded GitHub Actions CI

## Deferred

See [../tech-debt-tracker.md](../tech-debt-tracker.md) (split `client.py`,
shared test fakes, stricter mypy).
