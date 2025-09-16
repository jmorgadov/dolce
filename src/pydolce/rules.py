from dataclasses import dataclass
from typing import Callable

from pydolce.parser import CodeSegment, CodeSegmentReport, DocStatus


@dataclass
class DocRule:
    ref: str
    description: str
    prompt: str | None = None
    check: Callable[[CodeSegment], bool] | None = None

    @property
    def level(self) -> int:
        return int(self.ref[3])

    @property
    def number(self) -> int:
        return int(self.ref[3:])

    @property
    def sub_number(self) -> int:
        return int(self.ref[4:])


ALL_RULES = [
    DocRule(
        ref="DOC200",
        description="Docstring description contains spelling errors.",
        prompt="The docstring DESCRIPTION contains TYPOS. Exmaples: 'functon' instead of 'function', 'retrun' instead of 'return'. Report the specific typos. Scopes: [DESCRIPTION]",
    ),
    DocRule(
        ref="DOC201",
        description="Docstring parameter description contains spelling errors.",
        prompt="The description of some PARAMETERS contains TYPOS. Exmaples: 'functon' instead of 'function', 'retrun' instead of 'return'. Report the specific typos. Scopes: [PARAM_DESCRIPTION]",
    ),
    DocRule(
        ref="DOC202",
        description="Docstring return description contains spelling errors.",
        prompt="The description of the RETURN VALUE contains TYPOS. Exmaples: 'functon' instead of 'function', 'retrun' instead of 'return'. Report the specific typos. Scopes: [RETURN_DESCRIPTION]",
    ),
    DocRule(
        ref="DOC300",
        description="Docstring states the function does something that the code does not do.",
        prompt="The docstring summary does not match with the code summary. For example, the docstring says 'This function sends an email', but the code sends an SMS. Scopes: [DOCSTRING, CODE]",
    ),
    DocRule(
        ref="DOC301",
        description="Docstring omits a critical behavior that the code performs.",
        prompt="The code performs a CRITICAL behavior X, but the docstring does not mention this behavior. CRITICAL means heavy tasks. Non critical behavior may no be documented. Scopes: [DESCRIPTION, CODE]",
    ),
]

RULES_FROM_REF = {r.ref: r for r in ALL_RULES}


class RuleSet:
    def __init__(
        self, target: list[str] | None = None, disable: list[str] | None = None
    ):
        if target is None:
            target = list(RULES_FROM_REF.keys())
        if disable is None:
            disable = []

        self.rules = [
            rule for rule in ALL_RULES if rule.ref in target and rule.ref not in disable
        ]

        self.by_level: dict = {}
        for rule in self.rules:
            self.by_level.setdefault(rule.level, []).append(rule)

    def __hash__(self) -> int:
        return hash(tuple(sorted(r.ref for r in self.rules)))

    def contains_llm_rules(self) -> bool:
        return any(r.prompt is not None for r in self.rules)

    def llm_rules(self) -> list[DocRule]:
        return [r for r in self.rules if r.prompt is not None]

    def check(self, segment: CodeSegment) -> list[str]:
        issues = []
        for rule in self.rules:
            if rule.check is not None:
                if not rule.check(segment):
                    issues.append(f"{rule.ref}: {rule.description}")
        return issues


DEFAULT_RULESET = RuleSet()
