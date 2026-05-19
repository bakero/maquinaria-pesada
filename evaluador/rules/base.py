"""Tipos base para findings del evaluador."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    HARD = "hard"
    SOFT = "soft"


@dataclass
class Finding:
    code: str
    severity: Severity
    message: str
    line: int | None = None
    speaker: str | None = None
    snippet: str | None = None
    section: str | None = None
    autofixable: bool = False

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "line": self.line,
            "speaker": self.speaker,
            "section": self.section,
            "snippet": self.snippet,
            "message": self.message,
            "autofixable": self.autofixable,
        }


def hard(code: str, message: str, **kw) -> Finding:
    return Finding(code=code, severity=Severity.HARD, message=message, **kw)


def soft(code: str, message: str, **kw) -> Finding:
    return Finding(code=code, severity=Severity.SOFT, message=message, **kw)
