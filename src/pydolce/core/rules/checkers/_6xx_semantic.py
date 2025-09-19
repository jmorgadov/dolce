from pathlib import Path

from pydolce.core.parser import CodeSegment, Scopes
from pydolce.core.rules.rules import Rule, RuleContext

_INDEX = int(Path(__file__).stem[1]) * 100


def _id(n: int) -> int:
    return _INDEX + n


@Rule.llm_register(
    _id(1),
    "Description is not consistent with the function implementation.",
    scopes=Scopes.functions(),
)
def func_behavior_mismatch(segment: CodeSegment, _ctx: RuleContext) -> str | None:
    return (
        "The docstring summary does not match with the code summary. For example, the docstring says "
        "'This function sends an email', but the code sends an SMS. Scopes: [DOCSTRING, CODE]"
    )


@Rule.llm_register(
    _id(2), "Critical behavior not documented.", scopes=Scopes.functions()
)
def func_critical_behavior_omited(
    segment: CodeSegment, _ctx: RuleContext
) -> str | None:
    return (
        "The code performs a CRITICAL behavior X, but the docstring does not mention this behavior. "
        "CRITICAL means heavy tasks. Non critical behavior may no be documented. Scopes: [DESCRIPTION, CODE]"
    )
