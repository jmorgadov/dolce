from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, ClassVar, Generator, Iterable

from pydolce.parser import CodeSegment

DEFAULT_PREFIX = "DCE"


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
    def from_bool(passed: bool, issue: str | None = None) -> RuleResult:
        if passed:
            return RuleResult.good()
        return RuleResult.bad([issue] if issue else [])


_GROUPS = {
    1: "Structural",
    2: "Signature",
    3: "Content",
    4: "Integrity",
    6: "Semantic",
}


class Rule:
    all_rules: ClassVar[dict[str, Rule]] = {}

    def __init__(
        self,
        code: int,
        name: str,
        description: str,
        prompt: Callable[[CodeSegment], tuple[bool, str]] | None = None,
        check: Callable[[CodeSegment], RuleResult] | None = None,
    ):
        self.name = name
        self.code = code
        self.ref = f"{DEFAULT_PREFIX}{code:03d}"
        self.description = description
        self.prompt = prompt
        self.check = check
        self.group = code // 100

    @property
    def group_name(self) -> str:
        return _GROUPS.get(self.group, "Unknown")

    @classmethod
    def _register(cls, rule: Rule) -> None:
        assert rule.ref not in cls.all_rules, f"Rule {rule.ref} already registered"
        cls.all_rules[rule.ref] = rule

    @classmethod
    def register(cls, code: int, description: str) -> Callable:
        def decorator(func: Callable[[CodeSegment], RuleResult]) -> Callable:
            rule_name = func.__name__.replace("_", "-")
            rule = Rule(code, rule_name, description, check=func)
            cls._register(rule)
            func.__dict__["rule_ref"] = rule.ref
            return func

        return decorator

    @classmethod
    def llm_register(cls, code: int, description: str) -> Callable:
        def decorator(func: Callable[[CodeSegment], tuple[bool, str]]) -> Callable:
            rule_name = func.__name__.replace("_", "-")
            rule = Rule(code, rule_name, description, prompt=func)
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
        return any(r.prompt is not None for r in self.rules)

    def llm_rules(self) -> list[Rule]:
        return [r for r in self.rules if r.prompt is not None]

    def check(self, segment: CodeSegment) -> list[str]:
        issues = []
        for rule in self.rules:
            if rule.check is not None:
                result = rule.check(segment)
                if result.passed:
                    continue
                if not result.issues:
                    issues.append(f"{rule.ref}: {rule.description}")
                    continue
                for error in result.issues:
                    issues.append(f"{rule.ref}: {rule.description} ({error})")
        return issues
