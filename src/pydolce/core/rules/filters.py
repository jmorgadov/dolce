from typing import Iterable

from pydolce.core.rules.rule import LLMRule, StaticRule
from pydolce.core.rules.rulesets import RuleSet


def only(references: Iterable[str], rs: RuleSet) -> RuleSet:
    """Filter rules to only include those whose names are in the references."""
    refs = set(references)
    return filter(lambda r: r.reference in refs, rs)


def exclude(references: Iterable[str], rs: RuleSet) -> RuleSet:
    """Filter rules to exclude those whose names are in the references."""
    refs = set(references)
    return filter(lambda r: r.reference not in refs, rs)


def only_static(rs: RuleSet) -> RuleSet:
    """Filter rules to only include static rules (non-LLM)."""
    return filter(lambda r: isinstance(r, StaticRule), rs)


def only_llm(rs: RuleSet) -> RuleSet:
    """Filter rules to only include LLM-based rules."""
    return filter(lambda r: isinstance(r, LLMRule), rs)


def only_from_groups(groups: Iterable[int], rs: RuleSet) -> RuleSet:
    """Filter rules to only include those from the specified groups."""
    return filter(lambda r: r.group.value in set(groups), rs)
