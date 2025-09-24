from pydolce.core.parser import CodeSegment
from pydolce.core.rules.checkers.common import CheckContext


def func_behavior_mismatch(segment: CodeSegment, _ctx: CheckContext) -> str | None:
    """Function behavior described in the docstring does not match the actual code behavior"""
    return (
        "The docstring summary does not match with the code summary. For example, the docstring says "
        "'This function sends an email', but the code sends an SMS. Scopes: [DOCSTRING, CODE]"
    )


def func_critical_behavior_omited(
    segment: CodeSegment, _ctx: CheckContext
) -> str | None:
    """Function performs critical behavior not mentioned in the docstring"""
    return (
        "The code performs a CRITICAL behavior X, but the docstring does not mention this behavior. "
        "CRITICAL means heavy tasks. Non critical behavior may no be documented. Scopes: [DESCRIPTION, CODE]"
    )
