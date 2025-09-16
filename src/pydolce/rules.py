from dataclasses import dataclass
from typing import Callable

from pydolce.parser import CodeSegment


@dataclass
class DocRule:
    ref: str
    description: str
    prompt: str | None = None
    check: Callable[[CodeSegment], list[str]] | None = None

    @property
    def level(self) -> int:
        return int(self.ref[3])

    @property
    def number(self) -> int:
        return int(self.ref[3:])

    @property
    def sub_number(self) -> int:
        return int(self.ref[4:])


def check_params_type(segment: CodeSegment) -> list[str]:
    """
    Check if the parameter types in the docstring match the function signature.
    """

    if segment.annotations is None or not segment.annotations:
        return []

    if segment.parsed_doc is None:
        return []

    errors = []
    for param in segment.parsed_doc.params:
        p_name = param.arg_name
        p_type = param.type_name
        if p_type is None:
            # If the type is not documented, skip the check for this parameter
            # There is another rule to check for missing types
            continue

        if p_name not in segment.annotations:
            # Parameter documented but not in signature
            # There is another rule to check for missing parameters
            continue

        sig_type = segment.annotations.get(p_name)
        if sig_type is None:
            sig_type = "None"

        if str(sig_type).lower() != p_type.lower():
            errors.append(
                f"Parameter '{p_name}' has type '{sig_type}' in signature but '{p_type}' in docstring."
            )

    return errors


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
        description="Docstring parameter type is wrong.",
        check=check_params_type,
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
                for error in rule.check(segment):
                    issues.append(f"{rule.ref}: {rule.description} ({error})")
        return issues


DEFAULT_RULESET = RuleSet()
