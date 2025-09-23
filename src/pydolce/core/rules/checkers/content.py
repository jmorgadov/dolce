from pydolce.core.parser import CodeSegment
from pydolce.core.rules.checkers.common import CheckContext


def description_spelling(segment: CodeSegment, _ctx: CheckContext) -> str | None:
    return (
        "The docstring DESCRIPTION contains TYPOS. Examples: 'functon' instead of 'function', "
        "'retrun' instead of 'return'. Report the specific typos. Scopes: [DESCRIPTION]"
    )


def param_desc_spelling(segment: CodeSegment, _ctx: CheckContext) -> str | None:
    return (
        "The description of some PARAMETERS contains TYPOS. Examples: 'functon' instead of 'function', "
        "'retrun' instead of 'return'. Report the specific typos. Scopes: [PARAM_DESCRIPTION]"
    )


def return_desc_spelling(segment: CodeSegment, _ctx: CheckContext) -> str | None:
    return (
        "The description of the RETURN VALUE contains TYPOS. Examples: 'functon' instead of 'function', "
        "'retrun' instead of 'return'. Report the specific typos. Scopes: [RETURN_DESCRIPTION]"
    )
