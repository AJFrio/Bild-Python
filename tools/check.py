#!/usr/bin/env python3
"""Run harness linters, or the full local gate with --all."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.linters import (  # noqa: E402
    check_architecture,
    check_docs_structure,
    check_taste,
)


def run_harness() -> int:
    violations = []
    violations.extend(check_docs_structure())
    violations.extend(check_architecture())
    violations.extend(check_taste())
    if not violations:
        print("Harness linters: ok")
        return 0
    print(f"Harness linters: {len(violations)} violation(s)\n")
    for item in violations:
        print(item.format())
    return 1


def run_command(args: list[str]) -> int:
    print("+", " ".join(args))
    completed = subprocess.run(args, cwd=ROOT)
    return completed.returncode


def run_all() -> int:
    steps = [
        [sys.executable, "-m", "ruff", "format", "--check", "."],
        [sys.executable, "-m", "ruff", "check", "."],
        [sys.executable, "-m", "mypy", "bild"],
    ]
    for step in steps:
        code = run_command(step)
        if code != 0:
            print(
                "REMEDIATION: Fix the tool output above, then re-run "
                "`python tools/check.py --all`. "
                "Use `ruff format .` to apply formatting."
            )
            return code
    code = run_harness()
    if code != 0:
        return code
    return run_command([sys.executable, "-m", "pytest", "tests", "-q"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Bild-Python engineering harness")
    parser.add_argument(
        "--all",
        action="store_true",
        help="format check, ruff, mypy, harness linters, pytest",
    )
    args = parser.parse_args()
    return run_all() if args.all else run_harness()


if __name__ == "__main__":
    raise SystemExit(main())
