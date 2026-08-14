from __future__ import annotations

from .common import ROOT, Violation

AGENTS_MAX_LINES = 130

REQUIRED_DOCS = (
    "AGENTS.md",
    "AGENT_SETUP.md",
    "AGENT_USAGE.md",
    "ARCHITECTURE.md",
    "docs/INDEX.md",
    "docs/PRODUCT.md",
    "docs/DESIGN.md",
    "docs/CONVENTIONS.md",
    "docs/QUALITY_SCORE.md",
    "docs/SECURITY.md",
    "docs/RELIABILITY.md",
    "docs/design-docs/index.md",
    "docs/design-docs/core-beliefs.md",
    "docs/design-docs/http-client.md",
    "docs/design-docs/auth.md",
    "docs/exec-plans/active/README.md",
    "docs/exec-plans/completed/README.md",
    "docs/exec-plans/tech-debt-tracker.md",
    "docs/product-specs/index.md",
    "docs/product-specs/python-sdk.md",
    "docs/references/bild-api.md",
    "docs/references/harness-commands.md",
    "docs/references/eval-harness.md",
)

AGENTS_MUST_MENTION = (
    "docs/PRODUCT.md",
    "ARCHITECTURE.md",
    "docs/CONVENTIONS.md",
    "docs/INDEX.md",
    "AGENT_SETUP.md",
    "AGENT_USAGE.md",
    "tools/check.py",
    "Content-Type",
)

INDEX_MUST_LINK = (
    "ARCHITECTURE.md",
    "PRODUCT.md",
    "DESIGN.md",
    "CONVENTIONS.md",
    "QUALITY_SCORE.md",
    "SECURITY.md",
    "RELIABILITY.md",
)


def check_docs_structure() -> list[Violation]:
    violations: list[Violation] = []

    for relative in REQUIRED_DOCS:
        path = ROOT / relative
        if not path.is_file():
            violations.append(
                Violation(
                    rule="docs.required_file",
                    path=relative,
                    message="Required knowledge-base file is missing.",
                    remediation=(
                        f"Create {relative} with the topic implied by its path, "
                        "then add a row in docs/INDEX.md. See docs/INDEX.md and "
                        "AGENTS.md for the catalog pattern."
                    ),
                )
            )

    agents = ROOT / "AGENTS.md"
    if agents.is_file():
        text = agents.read_text(encoding="utf-8")
        line_count = len(text.splitlines())
        if line_count > AGENTS_MAX_LINES:
            violations.append(
                Violation(
                    rule="docs.agents_length",
                    path="AGENTS.md",
                    message=f"AGENTS.md has {line_count} lines; limit is {AGENTS_MAX_LINES}.",
                    remediation=(
                        "Move detailed guidance into docs/ and leave AGENTS.md as a "
                        "map with pointers. Update docs/INDEX.md if you add a file."
                    ),
                )
            )
        for needle in AGENTS_MUST_MENTION:
            if needle not in text:
                violations.append(
                    Violation(
                        rule="docs.agents_pointer",
                        path="AGENTS.md",
                        message=f"AGENTS.md does not mention {needle}.",
                        remediation=(
                            f"Add a pointer to {needle} in the Start here table or "
                            "Invariants section so agents can find it without a full-repo search."
                        ),
                    )
                )

    index = ROOT / "docs" / "INDEX.md"
    if index.is_file():
        index_text = index.read_text(encoding="utf-8")
        for needle in INDEX_MUST_LINK:
            if needle not in index_text:
                violations.append(
                    Violation(
                        rule="docs.index_link",
                        path="docs/INDEX.md",
                        message=f"docs/INDEX.md does not reference {needle}.",
                        remediation=(f"Add a catalog row in docs/INDEX.md that links to {needle}."),
                    )
                )

    return violations
