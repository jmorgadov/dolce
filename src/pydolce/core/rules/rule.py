from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from pydolce.core.parser import CodeSegmentType
from pydolce.types import LLMRulePrompter, RuleChecker

DEFAULT_PREFIX = "DCE"


class RuleGroup(IntEnum):
    STRUCTURAL = 1
    STYLE = 2
    SIGNATURE = 3
    CONTENT = 4
    SEMANTIC = 5


@dataclass
class Rule:
    code: int
    description: str
    checker: RuleChecker | None = None
    prompter: LLMRulePrompter | None = None
    scopes: list[CodeSegmentType] | None = None

    @property
    def name(self) -> str:
        if function := (self.checker or self.prompter):
            return function.__name__.replace("_", "-")
        raise ValueError("Rule must have either a checker or a prompter")

    @property
    def reference(self) -> str:
        return f"{DEFAULT_PREFIX}{self.code:03d}"

    @property
    def group(self) -> RuleGroup:
        return RuleGroup(self.code // 100)


# class Rule:
#     all_rules: ClassVar[dict[str, Rule]] = {}
#     default_rules: ClassVar[set[str]] = set()
#     llm_rules: ClassVar[set[str]] = set()

#     """
#     Migration schema from pydoclint. Keys are pydoclint rule reference, values
#     are corresponding pydolce rule references.
#     """
#     pydoclint_mig: ClassVar[dict[str, str]] = {}  # Will be filled at rule registration

#     """
#     Migration schema to from pydocstyle. Keys are pydolce rule reference,
#     values are corresponding pydocstyle rule references.
#     """
#     pydocstyle_mig: ClassVar[dict[str, str]] = {}  # Will be filled at rule registration

#     """
#     Migration schema from docsig. Keys are docsig rule reference, values are
#     corresponding pydolce rule references.
#     """
#     docsig_mig: ClassVar[dict[str, str]] = {}  # Will be filled at rule registration

#     def __init__(
#         self,
#         code: int,
#         name: str,
#         description: str,
#         prompter: LLMRulePrompter | None = None,
#         checker: RuleChecker | None = None,
#         scopes: list[CodeSegmentType] | None = None,
#     ):
#         """
#         A rule for checking docstrings.
#         """
#         self.name = name
#         self.code = code
#         self.ref = f"{DEFAULT_PREFIX}{code:03d}"
#         self.description = description
#         self.prompter = prompter
#         self.checker = checker
#         self.group = code // 100
#         self.scopes = scopes

#     @property
#     def group_name(self) -> str:
#         return _GROUPS.get(self.group, "Unknown")

#     @classmethod
#     def _register(cls, rule: Rule, default_enabled: bool) -> None:
#         assert rule.ref not in cls.all_rules, f"Rule {rule.ref} already registered"
#         cls.all_rules[rule.ref] = rule
#         if default_enabled:
#             cls.default_rules.add(rule.ref)

#     @classmethod
#     def _pydoclint_mig_register(cls, pydoclint_rule: str, rule_ref: str) -> None:
#         assert pydoclint_rule not in cls.pydoclint_mig, (
#             f"Pydoclint rule {pydoclint_rule} already mapped to {cls.pydoclint_mig[pydoclint_rule]}"
#         )
#         cls.pydoclint_mig[pydoclint_rule] = rule_ref

#     @classmethod
#     def _pydocstyle_mig_register(cls, pydocstyle_rule: str, rule_ref: str) -> None:
#         assert rule_ref not in cls.pydocstyle_mig, (
#             f"Pydolce rule {rule_ref} already mapped to {cls.pydocstyle_mig[rule_ref]}"
#         )
#         cls.pydocstyle_mig[rule_ref] = pydocstyle_rule

#     @classmethod
#     def _docsig_mig_register(cls, docsig_rule: str, rule_ref: str) -> None:
#         assert docsig_rule not in cls.docsig_mig, (
#             f"Docsig rule {docsig_rule} already mapped to {cls.docsig_mig[docsig_rule]}"
#         )
#         cls.docsig_mig[docsig_rule] = rule_ref

#     @classmethod
#     def register(
#         cls,
#         code: int,
#         description: str,
#         pydoclint_rule: str | None = None,
#         pydocstyle_rule: str | None = None,
#         docsig_rule: str | None = None,
#         scopes: list[CodeSegmentType] | None = None,
#         default_enabled: bool = True,
#     ) -> Callable:
#         def decorator(func: RuleChecker) -> Callable:
#             rule_name = func.__name__.replace("_", "-")
#             rule = Rule(code, rule_name, description, checker=func, scopes=scopes)

#             cls._register(rule, default_enabled)
#             if pydoclint_rule is not None:
#                 cls._pydoclint_mig_register(pydoclint_rule, rule.ref)

#             if pydocstyle_rule is not None:
#                 cls._pydocstyle_mig_register(pydocstyle_rule, rule.ref)

#             if docsig_rule is not None:
#                 cls._docsig_mig_register(docsig_rule, rule.ref)

#             func.__dict__["rule_ref"] = rule.ref
#             return func

#         return decorator

#     @classmethod
#     def llm_register(
#         cls,
#         code: int,
#         description: str,
#         scopes: list[CodeSegmentType] | None = None,
#         default_enabled: bool = True,
#     ) -> Callable:
#         def decorator(func: LLMRulePrompter) -> Callable:
#             rule_name = func.__name__.replace("_", "-")
#             rule = Rule(code, rule_name, description, prompter=func, scopes=scopes)
#             cls._register(rule, default_enabled)
#             cls.llm_rules.add(rule.ref)
#             func.__dict__["rule_ref"] = rule.ref
#             return func

#         return decorator

#     @classmethod
#     def is_ref_registered(cls, ref: str) -> bool:
#         return ref in cls.all_rules

#     def aplicable_to(self, seg_type: CodeSegmentType) -> bool:
#         if self.scopes is None:
#             return True
#         return seg_type in self.scopes


# class RuleSet:
#     def __init__(
#         self,
#         target: list[str] | set[str] | None = None,
#         disable: list[str] | set[str] | None = None,
#     ):
#         if target is None:
#             target = Rule.default_rules
#         if disable is None:
#             disable = set()

#         self._semgent_types: set[CodeSegmentType] = set()
#         self.rules: list[Rule] = []
#         self._set_rules(
#             [
#                 rule
#                 for rule in Rule.all_rules.values()
#                 if rule.ref in target and rule.ref not in disable
#             ]
#         )

#     def _set_rules(self, rules: list[Rule]) -> None:
#         self.rules = rules
#         self._semgent_types = {
#             seg_type for rule in self.rules for seg_type in rule.scopes or Scopes.all()
#         }

#     def applicable_to(self, segment: CodeSegment) -> bool:
#         return segment.seg_type in self._semgent_types

#     def remove_llm_rules(self) -> None:
#         self._set_rules([r for r in self.rules if r.prompter is None])

#     def is_dafualt(self) -> bool:
#         return len(self.rules) == len(Rule.all_rules)

#     def hash(self) -> str:
#         sorted_rules = sorted(r.ref for r in self.rules)
#         hasher = hashlib.sha256()
#         hasher.update(",".join(sorted_rules).encode("utf-8"))
#         return hasher.hexdigest()

#     def contains_llm_rules(self) -> bool:
#         return any(r.prompter is not None for r in self.rules)

#     def llm_rules(self) -> list[Rule]:
#         return [r for r in self.rules if r.prompter is not None]

#     def check(self, segment: CodeSegment, ctx: CheckContext) -> list[str]:
#         issues = []
#         for rule in self.rules:
#             if rule.checker is not None and rule.aplicable_to(segment.seg_type):
#                 result = rule.checker(segment, ctx)
#                 if result is None or result.passed:
#                     continue
#                 if not result.issues:
#                     issues.append(f"{rule.ref}: {rule.description}")
#                     continue
#                 for error in result.issues:
#                     issues.append(f"{rule.ref}: {rule.description} ({error})")
#         return issues
