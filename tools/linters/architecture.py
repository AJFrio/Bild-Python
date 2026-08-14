from __future__ import annotations

import ast
import re

from .common import ROOT, Violation

PUBLIC_EXPORTS = ("BildClient", "BildAPIError", "BildAuthError")
ALLOWED_BILD_MODULES = {"__init__", "client", "errors"}


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def check_architecture() -> list[Violation]:
    violations: list[Violation] = []
    bild_dir = ROOT / "bild"
    if not bild_dir.is_dir():
        return [
            Violation(
                rule="arch.package_missing",
                path="bild/",
                message="The bild package directory is missing.",
                remediation="Restore the bild/ package with __init__.py, client.py, and errors.py.",
            )
        ]

    for path in sorted(bild_dir.glob("*.py")):
        if path.stem not in ALLOWED_BILD_MODULES and path.stem != "__init__":
            violations.append(
                Violation(
                    rule="arch.unexpected_module",
                    path=f"bild/{path.name}",
                    message=f"Unexpected top-level module {path.name}.",
                    remediation=(
                        "New modules need a design doc and an update to "
                        "ALLOWED_BILD_MODULES in tools/linters/architecture.py plus "
                        "ARCHITECTURE.md. Prefer adding a resource method on an "
                        "existing *API class, or land the bild/resources/ split "
                        "(TD-1) instead of a one-off file."
                    ),
                )
            )

    init_src = _read("bild/__init__.py")
    if "import requests" in init_src or "from requests" in init_src:
        violations.append(
            Violation(
                rule="arch.init_requests",
                path="bild/__init__.py",
                message="Public surface imports requests.",
                remediation="Keep bild/__init__.py as re-exports of BildClient and errors only.",
            )
        )
    for name in PUBLIC_EXPORTS:
        if name not in init_src:
            violations.append(
                Violation(
                    rule="arch.public_export",
                    path="bild/__init__.py",
                    message=f"{name} is not exported from bild/__init__.py.",
                    remediation=(
                        f"Import and include {name} in __all__. Public surface must stay "
                        f"{set(PUBLIC_EXPORTS)} unless docs/product-specs/python-sdk.md "
                        "and this linter are updated together."
                    ),
                )
            )

    errors_src = _read("bild/errors.py")
    if "bild.client" in errors_src or "from .client" in errors_src:
        violations.append(
            Violation(
                rule="arch.errors_import_client",
                path="bild/errors.py",
                message="errors.py imports the client (layering violation).",
                remediation=(
                    "errors.py may only use the stdlib. Move any client-aware logic to client.py."
                ),
            )
        )
    if "import requests" in errors_src or "from requests" in errors_src:
        violations.append(
            Violation(
                rule="arch.errors_import_requests",
                path="bild/errors.py",
                message="errors.py imports requests.",
                remediation="Keep exception types independent of the HTTP library.",
            )
        )

    client_src = _read("bild/client.py")
    if re.search(r"session\.headers\.update\([\s\S]*Content-Type", client_src):
        violations.append(
            Violation(
                rule="arch.session_content_type",
                path="bild/client.py",
                message="Session headers set Content-Type.",
                remediation=(
                    "Remove Content-Type from session.headers. Bild treats that header "
                    "as 'this request has a JSON body' and GET/DELETE then 500. Let "
                    "requests set Content-Type only when json= is passed. See "
                    "docs/design-docs/http-client.md."
                ),
            )
        )

    tree = ast.parse(client_src)
    api_classes: set[str] = set()
    resources_fields: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name.endswith("API"):
            api_classes.add(node.name)
        if isinstance(node, ast.ClassDef) and node.name == "_Resources":
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    resources_fields.add(item.target.id)

    if not api_classes:
        violations.append(
            Violation(
                rule="arch.no_api_classes",
                path="bild/client.py",
                message="No *API resource classes found.",
                remediation=(
                    "Resource wrappers must be classes named <Group>API attached on _Resources."
                ),
            )
        )

    readme = _read("README.md")
    spec = _read("docs/product-specs/python-sdk.md")
    for field in sorted(resources_fields):
        token = f"client.api.{field}"
        if token not in readme and f"`{field}`" not in readme and field not in readme:
            violations.append(
                Violation(
                    rule="arch.readme_resource",
                    path="README.md",
                    message=f"Resource {field} is not mentioned in README.md.",
                    remediation=(
                        f"Add client.api.{field} to the README API groups list so "
                        "humans and agents discover it."
                    ),
                )
            )
        if field not in spec:
            violations.append(
                Violation(
                    rule="arch.spec_resource",
                    path="docs/product-specs/python-sdk.md",
                    message=f"Resource {field} is not listed in the product spec.",
                    remediation=(
                        f"Add `{field}` to the resource groups list in "
                        "docs/product-specs/python-sdk.md."
                    ),
                )
            )

    return violations
