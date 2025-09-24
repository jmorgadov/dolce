from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generator, Iterable

if TYPE_CHECKING:
    from pydolce.config import DolceConfig


@dataclass
class CheckResult:
    passed: bool
    issues: list[str]

    @staticmethod
    def good() -> CheckResult:
        return CheckResult(passed=True, issues=[])

    @staticmethod
    def bad(issues: list[str] | None = None) -> CheckResult:
        return CheckResult(passed=False, issues=issues or [])

    @staticmethod
    def bad_if_any(issues: list[str] | Iterable | Generator) -> CheckResult:
        if issues := list(issues):
            return CheckResult.bad(issues)
        return CheckResult.good()

    @staticmethod
    def check(passed: bool, issue: str | None = None) -> CheckResult:
        if passed:
            return CheckResult.good()
        return CheckResult.bad([issue] if issue else [])


@dataclass
class CheckContext:
    config: DolceConfig
