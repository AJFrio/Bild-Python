from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Violation:
    rule: str
    path: str
    message: str
    remediation: str

    def format(self) -> str:
        return (
            f"RULE: {self.rule}\n"
            f"PATH: {self.path}\n"
            f"MESSAGE: {self.message}\n"
            f"REMEDIATION: {self.remediation}\n"
        )


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()
