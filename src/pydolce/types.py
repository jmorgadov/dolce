from __future__ import annotations

from typing import Callable, Generator

from pydolce.core.parser import CodeSegment
from pydolce.core.rules.checkers.common import CheckContext, CheckResult

RuleChecker = Callable[[CodeSegment, CheckContext], Generator[CheckResult]]
LLMRulePrompter = Callable[[CodeSegment, CheckContext], str | None]
