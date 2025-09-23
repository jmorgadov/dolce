from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Iterable

if TYPE_CHECKING:
    from pydolce.core.rules.rule import Rule

from pydolce.core.parser import CodeSegment
from pydolce.core.rules.checkers.common import CheckContext, CheckResult

RuleChecker = Callable[[CodeSegment, CheckContext], CheckResult | None]
LLMRulePrompter = Callable[[CodeSegment, CheckContext], str | None]
RuleSet = Iterable[Rule]
