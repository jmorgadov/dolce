from pathlib import Path

from pydolce.parser import CodeSegment
from pydolce.rules.rules import Rule, RuleContext

_INDEX = int(Path(__file__).stem[1]) * 100


def _id(n: int) -> int:
    return _INDEX + n


@Rule.llm_register(_id(1), "Docstring description contains spelling errors.")
def description_spelling(segment: CodeSegment, _ctx: RuleContext) -> str | None:
    return (
        "The docstring DESCRIPTION contains TYPOS. Examples: 'functon' instead of 'function', "
        "'retrun' instead of 'return'. Report the specific typos. Scopes: [DESCRIPTION]"
    )


@Rule.llm_register(_id(2), "Docstring parameter description contains spelling errors.")
def param_desc_spelling(segment: CodeSegment, _ctx: RuleContext) -> str | None:
    return (
        "The description of some PARAMETERS contains TYPOS. Examples: 'functon' instead of 'function', "
        "'retrun' instead of 'return'. Report the specific typos. Scopes: [PARAM_DESCRIPTION]"
    )


@Rule.llm_register(_id(3), "Docstring return description contains spelling errors.")
def return_desc_spelling(segment: CodeSegment, _ctx: RuleContext) -> str | None:
    return (
        "The description of the RETURN VALUE contains TYPOS. Examples: 'functon' instead of 'function', "
        "'retrun' instead of 'return'. Report the specific typos. Scopes: [RETURN_DESCRIPTION]"
    )
