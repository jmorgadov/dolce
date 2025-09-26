from __future__ import annotations

from enum import IntEnum
from typing import Generator

from pydolce.core.parser import CodeSegment, CodeSegmentType
from pydolce.core.rules.checkers.common import CheckContext, CheckResult
from pydolce.types import LLMRulePrompter, RuleChecker

DEFAULT_PREFIX = "DCE"


class RuleGroup(IntEnum):
    STRUCTURAL = 1
    STYLE = 2
    SIGNATURE = 3
    CONTENT = 4
    SEMANTIC = 5


class Rule:
    def __init__(
        self,
        code: int,
        validator: RuleChecker | LLMRulePrompter,
        scopes: list[CodeSegmentType] | None = None,
    ):
        self.code = code
        self.validator = validator
        self.scopes = scopes

    @property
    def name(self) -> str:
        return self.validator.__name__.replace("_", "-")

    @property
    def description(self) -> str:
        return self.validator.__doc__ or "No description provided"

    @property
    def reference(self) -> str:
        return f"{DEFAULT_PREFIX}{self.code:03d}"

    @property
    def group(self) -> RuleGroup:
        return RuleGroup(self.code // 100)

    def __hash__(self) -> int:
        return hash((self.reference, self.description))

    def __repr__(self) -> str:
        return f"<Rule {self.reference}: {self.name}>"


class StaticRule(Rule):
    def __init__(
        self,
        code: int,
        checker: RuleChecker,
        scopes: list[CodeSegmentType] | None = None,
    ):
        super().__init__(code, checker, scopes)

    def check(self, segment: CodeSegment, ctx: CheckContext) -> Generator[CheckResult]:
        result = self.validator(segment, ctx)
        assert isinstance(result, Generator)
        yield from result


class LLMRule(Rule):
    def __init__(
        self,
        code: int,
        prompter: LLMRulePrompter,
        scopes: list[CodeSegmentType] | None = None,
    ):
        super().__init__(code, prompter, scopes)

    def prompt(self, segment: CodeSegment, ctx: CheckContext) -> str | None:
        result = self.validator(segment, ctx)
        assert result is None or isinstance(result, str)
        return result
