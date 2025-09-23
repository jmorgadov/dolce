from typing import Iterable

from pydolce.types import RuleSet


def only(references: Iterable[str], rs: RuleSet) -> RuleSet:
    """Filter rules to only include those whose names are in the references."""
    refs = set(references)
    return filter(lambda r: r.reference in refs, rs)


def exclude(references: Iterable[str], rs: RuleSet) -> RuleSet:
    """Filter rules to exclude those whose names are in the references."""
    refs = set(references)
    return filter(lambda r: r.reference not in refs, rs)


def without_llm(rs: RuleSet) -> RuleSet:
    """Filter rules to only include static rules (non-LLM)."""
    return filter(lambda r: r.checker is not None, rs)


def only_llm(rs: RuleSet) -> RuleSet:
    """Filter rules to only include LLM-based rules."""
    return filter(lambda r: r.prompter is not None, rs)


def only_from_groups(groups: Iterable[int], rs: RuleSet) -> RuleSet:
    """Filter rules to only include those from the specified groups."""
    return filter(lambda r: r.group.value in set(groups), rs)
