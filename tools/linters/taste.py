from __future__ import annotations

import re

from .common import ROOT, Violation

MAX_LINES = {
    "bild/__init__.py": 40,
    "bild/errors.py": 40,
    "bild/client.py": 800,
}

SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "bild_python.egg-info",
    "dist",
    "build",
}

JWT_RE = re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")
ASSIGNED_KEY_RE = re.compile(
    r"BILD_API_KEY\s*=\s*['\"](?!YOUR_JWT_TOKEN)(?!your_token)(?!$)[^'\"]+['\"]",
    re.IGNORECASE,
)


def check_taste() -> list[Violation]:
    violations: list[Violation] = []

    for relative, limit in MAX_LINES.items():
        path = ROOT / relative
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) > limit:
            violations.append(
                Violation(
                    rule="taste.file_size",
                    path=relative,
                    message=f"{relative} has {len(lines)} lines; limit is {limit}.",
                    remediation=(
                        f"Split {relative} or raise the limit in tools/linters/taste.py "
                        "and document why in docs/exec-plans/tech-debt-tracker.md. "
                        "For client.py, prefer the bild/resources/ split (TD-1)."
                    ),
                )
            )

    client = ROOT / "bild" / "client.py"
    if client.is_file():
        src = client.read_text(encoding="utf-8")
        if re.search(r"^\s*print\(", src, re.MULTILINE):
            violations.append(
                Violation(
                    rule="taste.no_print",
                    path="bild/client.py",
                    message="Library code uses print().",
                    remediation=(
                        "Remove print() from bild/. Raise exceptions or return data to the caller."
                    ),
                )
            )
        if "time.sleep" in src:
            violations.append(
                Violation(
                    rule="taste.no_sleep",
                    path="bild/client.py",
                    message="Library code uses time.sleep.",
                    remediation=(
                        "Do not sleep inside the client. Let callers retry with their own backoff."
                    ),
                )
            )

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.suffix not in {".py", ".md", ".yml", ".yaml", ".toml", ".txt", ".env"}:
            continue
        if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.resolve().relative_to(ROOT).as_posix()
        if JWT_RE.search(text):
            violations.append(
                Violation(
                    rule="taste.jwt_literal",
                    path=rel,
                    message="File looks like it contains a real JWT.",
                    remediation=(
                        "Remove the token. Use YOUR_JWT_TOKEN in examples and test-token in tests."
                    ),
                )
            )
        if path.name != ".env.example" and ASSIGNED_KEY_RE.search(text):
            violations.append(
                Violation(
                    rule="taste.api_key_literal",
                    path=rel,
                    message=(
                        "File assigns a literal BILD_API_KEY that is not the example placeholder."
                    ),
                    remediation=(
                        "Delete the literal. Read the token from the environment "
                        "in tests and examples."
                    ),
                )
            )

    live = ROOT / "tests" / "test_live_api.py"
    if live.is_file():
        src = live.read_text(encoding="utf-8")
        forbidden = (
            ".invite(",
            ".remove(",
            ".delete(",
            ".create(",
            ".create_live(",
            ".create_static(",
            ".create_token(",
            ".checkout(",
            ".initiate(",
            ".complete(",
            ".release(",
            ".cancel(",
            ".update(",
            ".close(",
            ".move(",
            ".export_universal(",
        )
        for token in forbidden:
            if token in src:
                violations.append(
                    Violation(
                        rule="taste.live_readonly",
                        path="tests/test_live_api.py",
                        message=f"Live tests call a write/delete-style method: {token}.",
                        remediation=(
                            "Keep tests/test_live_api.py read-only (list/get/search). "
                            "Exercise writes only with a fake session in test_client_routes.py."
                        ),
                    )
                )

    return violations
