from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, ClassVar, Generator, Iterable

if TYPE_CHECKING:
    from pydolce.config import DolceConfig

import pydolce
from pydolce.parser import CodeSegment

DEFAULT_PREFIX = "DCE"


_GROUPS = {
    int(p.stem[1]): p.stem[5:].capitalize()
    for i, p in enumerate((Path(pydolce.rules.__path__[0]) / "checkers").glob("*.py"))
    if p.stem != "__init__"
}


@dataclass
class RuleResult:
    passed: bool
    issues: list[str]

    @staticmethod
    def good() -> RuleResult:
        return RuleResult(passed=True, issues=[])

    @staticmethod
    def bad(issues: list[str] | None = None) -> RuleResult:
        return RuleResult(passed=False, issues=issues or [])

    @staticmethod
    def bad_if_any(issues: list[str] | Iterable | Generator) -> RuleResult:
        issues = list(issues)
        if issues:
            return RuleResult.bad(issues)
        return RuleResult.good()

    @staticmethod
    def check(passed: bool, issue: str | None = None) -> RuleResult:
        if passed:
            return RuleResult.good()
        return RuleResult.bad([issue] if issue else [])


class RuleContext:
    def __init__(self, config: DolceConfig) -> None:
        self.config = config


RuleChecker = Callable[[CodeSegment, RuleContext], RuleResult | None]
LLMRulePrompter = Callable[[CodeSegment, RuleContext], str | None]


class Rule:
    all_rules: ClassVar[dict[str, Rule]] = {}

    """
    Migration schema from pydoclint. Keys are pydoclint rule reference, values
    are corresponding pydolce rule references.
    """
    pydoclint_mig: ClassVar[dict[str, str]] = {}  # Will be filled at rule registration

    """
    Migration schema to from pydocstyle. Keys are pydolce rule reference,
    values are corresponding pydocstyle rule references.
    """
    pydocstyle_mig: ClassVar[dict[str, str]] = {}  # Will be filled at rule registration

    """
    Migration schema from docsig. Keys are docsig rule reference, values are
    corresponding pydolce rule references.
    """
    docsig_mig: ClassVar[dict[str, str]] = {}  # Will be filled at rule registration

    def __init__(
        self,
        code: int,
        name: str,
        description: str,
        prompter: LLMRulePrompter | None = None,
        checker: RuleChecker | None = None,
    ):
        self.name = name
        self.code = code
        self.ref = f"{DEFAULT_PREFIX}{code:03d}"
        self.description = description
        self.prompter = prompter
        self.checker = checker
        self.group = code // 100

    @property
    def group_name(self) -> str:
        return _GROUPS.get(self.group, "Unknown")

    @classmethod
    def _register(cls, rule: Rule) -> None:
        assert rule.ref not in cls.all_rules, f"Rule {rule.ref} already registered"
        cls.all_rules[rule.ref] = rule

    @classmethod
    def _pydoclint_mig_register(cls, pydoclint_rule: str, rule_ref: str) -> None:
        assert pydoclint_rule not in cls.pydoclint_mig, (
            f"Pydoclint rule {pydoclint_rule} already mapped to {cls.pydoclint_mig[pydoclint_rule]}"
        )
        cls.pydoclint_mig[pydoclint_rule] = rule_ref

    @classmethod
    def _pydocstyle_mig_register(cls, pydocstyle_rule: str, rule_ref: str) -> None:
        assert rule_ref not in cls.pydocstyle_mig, (
            f"Pydolce rule {rule_ref} already mapped to {cls.pydocstyle_mig[rule_ref]}"
        )
        cls.pydocstyle_mig[rule_ref] = pydocstyle_rule

    @classmethod
    def _docsig_mig_register(cls, docsig_rule: str, rule_ref: str) -> None:
        assert docsig_rule not in cls.docsig_mig, (
            f"Docsig rule {docsig_rule} already mapped to {cls.docsig_mig[docsig_rule]}"
        )
        cls.docsig_mig[docsig_rule] = rule_ref

    @classmethod
    def register(
        cls,
        code: int,
        description: str,
        pydoclint_rule: str | None = None,
        pydocstyle_rule: str | None = None,
        docsig_rule: str | None = None,
    ) -> Callable:
        def decorator(func: RuleChecker) -> Callable:
            rule_name = func.__name__.replace("_", "-")
            rule = Rule(code, rule_name, description, checker=func)

            cls._register(rule)
            if pydoclint_rule is not None:
                cls._pydoclint_mig_register(pydoclint_rule, rule.ref)

            if pydocstyle_rule is not None:
                cls._pydocstyle_mig_register(pydocstyle_rule, rule.ref)

            if docsig_rule is not None:
                cls._docsig_mig_register(docsig_rule, rule.ref)

            func.__dict__["rule_ref"] = rule.ref
            return func

        return decorator

    @classmethod
    def llm_register(cls, code: int, description: str) -> Callable:
        def decorator(func: LLMRulePrompter) -> Callable:
            rule_name = func.__name__.replace("_", "-")
            rule = Rule(code, rule_name, description, prompter=func)
            cls._register(rule)
            func.__dict__["rule_ref"] = rule.ref
            return func

        return decorator

    @classmethod
    def is_ref_registered(cls, ref: str) -> bool:
        return ref in cls.all_rules


class RuleSet:
    def __init__(
        self, target: list[str] | None = None, disable: list[str] | None = None
    ):
        if target is None:
            target = list(Rule.all_rules.keys())
        if disable is None:
            disable = []

        self.rules = [
            rule
            for rule in Rule.all_rules.values()
            if rule.ref in target and rule.ref not in disable
        ]

    def __hash__(self) -> int:
        return hash(tuple(sorted(r.ref for r in self.rules)))

    def contains_llm_rules(self) -> bool:
        return any(r.prompter is not None for r in self.rules)

    def llm_rules(self) -> list[Rule]:
        return [r for r in self.rules if r.prompter is not None]

    def check(self, segment: CodeSegment, ctx: RuleContext) -> list[str]:
        issues = []
        for rule in self.rules:
            if rule.checker is not None:
                result = rule.checker(segment, ctx)
                if result is None or result.passed:
                    continue
                if not result.issues:
                    issues.append(f"{rule.ref}: {rule.description}")
                    continue
                for error in result.issues:
                    issues.append(f"{rule.ref}: {rule.description} ({error})")
        return issues
