from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Generator, Iterable

if TYPE_CHECKING:
    from pydolce.config import DolceConfig


class CheckStatus(Enum):
    GOOD = "good"
    BAD = "bad"
    UNKNOWN = "unknown"

    def __repr__(self) -> str:
        return self.value

    @staticmethod
    def from_str(s: str) -> CheckStatus:
        s = s.lower()
        if s == "good":
            return CheckStatus.GOOD
        elif s == "bad":
            return CheckStatus.BAD
        elif s == "unknown":
            return CheckStatus.UNKNOWN
        else:
            raise ValueError(f"Invalid CheckStatus: {s}")


@dataclass
class CheckResult:
    status: CheckStatus
    issue: str = ""

    @staticmethod
    def good() -> CheckResult:
        return CheckResult(status=CheckStatus.GOOD)

    @staticmethod
    def bad(issue: str = "") -> CheckResult:
        return CheckResult(status=CheckStatus.BAD, issue=issue)

    @staticmethod
    def unknown(issue: str = "") -> CheckResult:
        return CheckResult(status=CheckStatus.UNKNOWN, issue=issue)

    @staticmethod
    def from_issues(issue: Iterable[str]) -> Generator[CheckResult]:
        yield from (CheckResult.bad(i) for i in issue) or [CheckResult.good()]

    @staticmethod
    def check(passed: bool, issue: str = "") -> CheckResult:
        if passed:
            return CheckResult.good()
        return CheckResult.bad(issue)


@dataclass
class CheckContext:
    config: DolceConfig
