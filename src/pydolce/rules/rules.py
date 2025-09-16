from dataclasses import dataclass
from typing import Callable

from pydolce.parser import CodeSegment, CodeSegmentType
from pydolce.rules.checkers.duplicate_params import check_duplicate_params
from pydolce.rules.checkers.param_description import check_params_descr
from pydolce.rules.checkers.param_exist import check_params_exist
from pydolce.rules.checkers.param_missing import check_params_missing
from pydolce.rules.checkers.param_type_missing import check_params_type_missing
from pydolce.rules.checkers.param_types import check_params_type
from pydolce.rules.checkers.return_missing import check_return_missing
from pydolce.rules.checkers.return_type import check_return_type
from pydolce.rules.checkers.valid_syntax import check_valid_syntax


@dataclass
class DocRule:
    ref: str
    description: str
    prompt: str | None = None
    check: Callable[[CodeSegment], list[str] | None] | None = None

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
        ref="DOC101",
        description="Function is missing a docstring.",
        check=lambda segment: []
        if segment.seg_type == CodeSegmentType.Function and not segment.doc.strip()
        else None,
    ),
    DocRule(
        ref="DOC102",
        description="Class is missing a docstring.",
        check=lambda segment: []
        if segment.seg_type == CodeSegmentType.Class and not segment.doc.strip()
        else None,
    ),
    DocRule(
        ref="DOC103",
        description="Class docstring has invalid syntax.",
        check=check_valid_syntax,
    ),
    DocRule(
        ref="DOC201",
        description="Duplicate parameters in docstring.",
        check=check_duplicate_params,
    ),
    DocRule(
        ref="DOC202",
        description="Documented parameter does not exist",
        check=check_params_exist,
    ),
    DocRule(
        ref="DOC203",
        description="Missing parameter in documention",
        check=check_params_missing,
    ),
    DocRule(
        ref="DOC204",
        description="Parameter description is missing",
        check=check_params_descr,
    ),
    DocRule(
        ref="DOC205",
        description="Return missing from docstring",
        check=check_return_missing,
    ),
    DocRule(
        ref="DOC206",
        description="Parameter type missing",
        check=check_params_type_missing,
    ),
    DocRule(
        ref="DOC206",
        description="Invalid parameter type",
        check=check_params_type,
    ),
    DocRule(
        ref="DOC204",
        description="Invalid return type",
        check=check_return_type,
    ),
    DocRule(
        ref="DOC301",
        description="Docstring description contains spelling errors.",
        prompt="The docstring DESCRIPTION contains TYPOS. Exmaples: 'functon' instead of 'function', 'retrun' instead of 'return'. Report the specific typos. Scopes: [DESCRIPTION]",
    ),
    DocRule(
        ref="DOC302",
        description="Docstring parameter description contains spelling errors.",
        prompt="The description of some PARAMETERS contains TYPOS. Exmaples: 'functon' instead of 'function', 'retrun' instead of 'return'. Report the specific typos. Scopes: [PARAM_DESCRIPTION]",
    ),
    DocRule(
        ref="DOC303",
        description="Docstring return description contains spelling errors.",
        prompt="The description of the RETURN VALUE contains TYPOS. Exmaples: 'functon' instead of 'function', 'retrun' instead of 'return'. Report the specific typos. Scopes: [RETURN_DESCRIPTION]",
    ),
    DocRule(
        ref="DOC401",
        description="Docstring states the function does something that the code does not do.",
        prompt="The docstring summary does not match with the code summary. For example, the docstring says 'This function sends an email', but the code sends an SMS. Scopes: [DOCSTRING, CODE]",
    ),
    DocRule(
        ref="DOC402",
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
                errors = rule.check(segment)
                if errors is None:
                    continue
                if not errors:
                    issues.append(f"{rule.ref}: {rule.description}")
                    continue
                for error in errors:
                    issues.append(f"{rule.ref}: {rule.description} ({error})")
        return issues


DEFAULT_RULESET = RuleSet()
